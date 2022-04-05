#!/usr/bin/env python3
# This file is part of Conky-maker.
#
# Conky-maker is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Conky-maker is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with wijjet.  If not, see <https://www.gnu.org/licenses/>.


"""Conky-maker configuration generator for Conky desktop widgets."""

import argparse
import os
import re
import sys
from importlib.util import spec_from_file_location, module_from_spec
from typing import Any, List, Union, Tuple, Iterator, Optional, Dict

FONT_COLOR_REGEX = re.compile(r'[$]([{]?)(color|font)([^{]*[}]|\b)')

# This long bash command updates a file with the external IP every 4 hours and
# displays the external IP, either directly from a URL or from the cache file.
EXTERNAL_IP_COMMAND = \
    '[ $(( $(date +%%s) - $(test -f %(p)s && date -r %(p)s +%%s || echo 0) )) -gt %(r)d ]'\
    ' && { curl -s %(u)s | tee %(p)s; } || cat %(p)s' % {
        'p': os.path.expanduser('~/.external_ip'),
        'u': 'https://ifconfig.me/',
        'r': 14400}

BASE_CONFIGURATION = dict(
    background=True,
    use_xft=True,
    xftalpha=1,
    total_run_times=0,
    own_window=True,
    own_window_type='normal',
    own_window_hints='undecorated,below,sticky,skip_taskbar,skip_pager',
    own_window_argb_visual=True,
    own_window_argb_value=127,
    own_window_transparent=False,
    double_buffer=True,
    draw_shades=False,
    draw_outline=False,
    draw_borders=False,
    draw_graph_borders=True,
    no_buffers=True,
    uppercase=False,
    cpu_avg_samples=2,
    override_utf8_locale=False,
    short_units=True,
    default_shade_color='black',
)

DEFAULT_EXTERNAL_COMMAND_INTERVAL = 3600
DEFAULT_COLOR = 'ffffff'
DEFAULT_COLOR_OUTLINE = '808080'
DEFAULT_METER_WIDTH = 100
DEFAULT_METER_HEIGHT = 25
DEFAULT_BAR_WIDTH = 100
DEFAULT_BAR_HEIGHT = 10
DEFAULT_FONT = 'FreeSans:size=12'
DEFAULT_PLACEMENT = 'top_left'
DEFAULT_WINDOW_WIDTH_MIN = 200
DEFAULT_WINDOW_HEIGHT_MIN = 500
DEFAULT_WINDOW_OUTER_MARGIN = 20
DEFAULT_WINDOW_GAP = 10
DEFAULT_REFRESH_INTERVAL = 1


def abort(message: Any):
    """
    Display error and exit with error return code.

    :param message: error message to display
    """
    sys.stderr.write(f'ERROR: {message}{os.linesep}')
    sys.exit(1)


# ConfigDict item type, which may be part of a recursive structure.
ConfigDictItem = Union['ConfigDict', List['ConfigDictItem'], Any]


class ConfigDict(dict):
    """Dictionary wrapper with alternate attribute access."""

    def __getattr__(self, name: str) -> Optional[Any]:
        """
        Attribute access wrapped for recursion.

        :param name: attribute name
        :return: attribute value or None if not present
        """
        return self._wrap_data(self.get(name))

    def __getitem__(self, name: str) -> Optional[Any]:
        """
        Dictionary element access wrapped for recursive attribute access.

        :param name: attribute name
        :return: attribute value or None if not present
        """
        return self._wrap_data(self.get(name))

    def items(self) -> Iterator[Tuple[str, ConfigDictItem]]:
        """
        Dictionary item iteration wrapped for attribute access.
        :return:
        """
        for name, value in super().items():
            yield name, self._wrap_data(value)

    @classmethod
    def _wrap_data(cls, data: Any) -> ConfigDictItem:
        # Wrap item as ConfigDict or list of wrapped items.
        if data is None:
            return cls({})
        if isinstance(data, dict):
            return cls(data)
        if isinstance(data, list):
            return [cls._wrap_data(item) for item in data]
        return data


class ConkyMaker:
    """
    Conky configuration generator.

    Modules must provide a concrete class named "Maker".

    Must be subclassed in order to provide a render() implementation.
    """

    def __init__(self, parameters: ConfigDict):
        """
        ConkyMaker constructor.

        :param parameters: parameters loaded from data file
        """
        self.parameters = parameters
        self.lines: List[str] = []
        self.colors: Dict[str, str] = {}
        self.fonts: Dict[str, str] = {}
        self.placement: str = DEFAULT_PLACEMENT
        self.window_width_min: int = DEFAULT_WINDOW_WIDTH_MIN
        self.window_height_min: int = DEFAULT_WINDOW_HEIGHT_MIN
        self.window_outer_margin: int = DEFAULT_WINDOW_OUTER_MARGIN
        self.window_gap: int = DEFAULT_WINDOW_GAP
        self.refresh_interval: int = DEFAULT_REFRESH_INTERVAL
        self.default_color: str = DEFAULT_COLOR
        self.default_color_outline: str = DEFAULT_COLOR_OUTLINE
        self.default_font: str = DEFAULT_FONT

    def configure_conky(self,
                        placement: str = None,
                        window_width_min: int = None,
                        window_height_min: int = None,
                        window_outer_margin: int = None,
                        window_gap: int = None,
                        refresh_interval: int = None,
                        default_color: str = None,
                        default_color_outline: str = None,
                        default_font: str = None,
                        ):
        """
        Configure Conky configuration options.

        :param placement: optional placement override
        :param window_width_min: optional minimum window width override
        :param window_height_min: optional minimum window height override
        :param window_outer_margin: optional window margin override
        :param window_gap: optional window gap override
        :param refresh_interval: optional refresh interval override
        :param default_color: optional default color override
        :param default_color_outline: optional default color_outline override
        :param default_font: optional default font override
        """
        if placement is not None:
            self.placement = placement
        if window_width_min is not None:
            self.window_width_min = window_width_min
        if window_height_min is not None:
            self.window_height_min = window_height_min
        if window_outer_margin is not None:
            self.window_outer_margin = window_outer_margin
        if window_gap is not None:
            self.window_gap = window_gap
        if refresh_interval is not None:
            self.refresh_interval = refresh_interval
        if default_color is not None:
            self.default_color = default_color
        if default_color_outline is not None:
            self.default_color_outline = default_color_outline
        if default_font is not None:
            self.default_font = default_font

    def color_theme(self, colors: Dict[str, str]):
        """
        Set or update color theme.

        :param colors: color name to string mappings
        """
        self.colors.update(colors)

    def font_theme(self, fonts: Dict[str, str]):
        """
        Set or update font theme.

        :param fonts: font name to string mappings
        """
        self.fonts.update(fonts)

    def line(self, *fields: str):
        """
        Add a complete line, given some fields.

        Automatically adds macros as needed to clear a changed color or font.

        :param fields: field strings
        """
        fields = list(fields)
        changed_color = changed_font = False
        for field in fields:
            for font_color_change in FONT_COLOR_REGEX.finditer(field):
                if font_color_change.group(2) == 'color':
                    changed_color = font_color_change.group(3) not in ('', '}')
                elif font_color_change.group(2) == 'font':
                    changed_font = font_color_change.group(3) not in ('', '}')
        if changed_color:
            fields.append(self.color_clear())
        if changed_font:
            fields.append(self.font_clear())
        self.lines.append(''.join(fields))

    def render(self):
        """Required render override."""
        raise NotImplementedError

    @staticmethod
    def text(value: Any) -> str:
        """
        Inject text or other value as string.

        :param value: input value
        :return: output string
        """
        return str(value)

    def color(self, color_spec: Optional[str]) -> str:
        """
        Inject ${color #XXXXXX) hex color macro.

        Returns '' if color_spec is None.

        :param color_spec: hex color string without leading '#', named theme
                           color, or None if no color change is needed
        :return: output string
        """
        if color_spec in self.colors:
            color_spec = self.colors[color_spec]
        if color_spec is None:
            return ''
        return '${color #%s}' % color_spec

    @staticmethod
    def color_index(index: int) -> str:
        """
        Inject ${colorN) to set a color by index number.

        :param index: color index (0-9)
        :return: output string
        """
        return '${color%d}' % index

    @staticmethod
    def color_clear() -> str:
        """
        Inject ${color} to restore default.

        :return: output string
        """
        return '${color}'

    def font(self, font_spec: Optional[str]) -> str:
        """
        Inject ${font...) to set a font or ${font} to restore default.

        :param font_spec: font specification, theme font name, or None if no
                          font change is needed
        :return: output string
        """
        if font_spec in self.fonts:
            font_spec = self.fonts[font_spec]
        if font_spec is None:
            return ''
        return '${font %s}' % font_spec

    @staticmethod
    def font_clear() -> str:
        """
        Inject ${font} to restore default.

        :return: output string
        """
        return '${font}'

    @staticmethod
    def center() -> str:
        """
        Inject centering (${alignc}) for subsequent items of current line.

        :return: output string
        """
        return '${alignc}'

    @staticmethod
    def right() -> str:
        """
        Inject right-justification (${alignr}) for subsequent items of current line.

        :return: output string
        """
        return '${alignr}'

    @staticmethod
    def time_date(time_date_format: str) -> str:
        """
        Inject time/date (${time...}).

        :param time_date_format: strftime-style time/date format string
        :return: output string
        """
        return '${time %s}' % time_date_format

    @staticmethod
    def horizontal_rule() -> str:
        """
        Inject horizontal rule (${hr}).

        :return: output string
        """
        return '${hr}'

    @staticmethod
    def offset(x: int = None, y: int = None) -> str:
        """
        Inject horizontal (${offset...}) and or vertical (${voffset...}).

        :param x: optional horizontal offset
        :param y: optional vertical offset
        :return: output string
        """
        parts: List[str] = []
        if x:
            parts.append('${offset %d}' % x)
        if y:
            parts.append('${voffset %d}' % y)
        return ''.join(parts)

    def meter(self,
              graph_type: str,
              width: int = None,
              height: int = None,
              param: str = None,
              graph_color1: str = None,
              graph_color2: str = None,
              border_color: str = None,
              ) -> str:
        """
        Inject meter (${...graph...}).

        :param graph_type: Conky graph type name, e.g. "cpugraph", "diskiograph"...
        :param width: optional graph width
        :param height: optional graph height
        :param param: optional graph parameter (varies by graph type)
        :param graph_color1: optional graph gradient color #1
        :param graph_color2: optional graph gradient color #2
        :param border_color: optional border color
        :return: output string
        """
        param_string = f' {param}' if param else ''
        if graph_color1:
            if graph_color2:
                graph_color_string = f' {graph_color1} {graph_color2}'
            else:
                graph_color_string = f' {graph_color1}'
        elif graph_color2:
            graph_color_string = f' {graph_color2}'
        else:
            graph_color_string = ''
        return '%s${%s%s %d,%d%s}' % (self.color(border_color),
                                      graph_type,
                                      param_string,
                                      height or DEFAULT_METER_HEIGHT,
                                      width or DEFAULT_METER_WIDTH,
                                      graph_color_string)

    def bar(self,
            bar_type: str,
            width: int = None,
            height: int = None,
            color: str = None,
            param: str = None,
            ) -> str:
        """
        Inject horizontal bar meter (${...bar...}).

        :param bar_type: Conky bar type name, e.g. "membar", "fs_bar"...
        :param width: optional bar width
        :param height: optional bar height
        :param color: optional bar color
        :param param: optional bar parameter (varies by bar type)
        :return: output string
        """
        param_string = f' {param}' if param else ''
        return '%s${%s %d,%d%s}' % (self.color(color),
                                    bar_type,
                                    height or DEFAULT_BAR_HEIGHT,
                                    width or DEFAULT_BAR_WIDTH,
                                    param_string)

    @staticmethod
    def exec(command: str, interval: int = None) -> str:
        """
        Inject output of external command (${exec...} or ${execi...}).

        Throttled if interval is not specified or > 0.

        If interval is explicitly zero it always runs during Conky refresh.

        :param command: external command
        :param interval: optional interval for throttling frequency of expensive command
        :return: output string
        """
        if interval == 0:
            return '${exec %s}' % command
        if interval is None:
            interval = DEFAULT_EXTERNAL_COMMAND_INTERVAL
        return '${execi %d %s}' % (interval, command)

    @staticmethod
    def host_name() -> str:
        """
        Inject host name (${nodename}).

        :return: output string
        """
        return '${nodename}'

    @staticmethod
    def kernel() -> str:
        """
        Inject Linux kernel name (${kernel}).

        :return: output string
        """
        return '${kernel}'

    @staticmethod
    def uptime(short: bool = False) -> str:
        """
        Inject uptime (${uptime} or ${uptime_short}).

        :param short: provide short form if set and True
        :return: output string
        """
        if short:
            return '${uptime_short}'
        return '${uptime}'

    @staticmethod
    def ip_address(device: str) -> str:
        """
        Inject IP address of network device (${addr...}).

        :param device: network device name
        :return: output string
        """
        return '${addr %s}' % device

    def mac_address(self, device: str, check_interval: int = None) -> str:
        """
        Inject MAC address of network device.

        Throttled by "interval_network_check" parameter.

        :param device: network device name
        :param check_interval: optional check interval
        :return: output string
        """
        return self.exec("ip addr show dev %s | awk '/link\\/ether/{print $2}'" % device,
                         interval=check_interval)

    def external_ip(self, check_interval: int = None) -> str:
        """
        Inject external IP address.

        Throttled by both the "interval_network_check" parameter and a 4 hour
        cache frequency.

        :param check_interval: optional check interval
        :return: output string
        """
        return self.exec(f'bash -c "{EXTERNAL_IP_COMMAND}"',
                         interval=check_interval)

    @staticmethod
    def cpu_percent(cpu_number: int) -> str:
        """
        Inject CPU usage percent (${cpu cpu...}).

        :param cpu_number: CPU number
        :return: output string
        """
        return '${cpu cpu %s}%%' % cpu_number

    def cpu_temperature(self, cpu_number: int, check_interval: int = None) -> str:
        """
        Inject CPU temperature (Celsius).

        Throttled by "interval_temperature_check" parameter.

        :param cpu_number: CPU number
        :param check_interval: optional check interval
        :return: output string
        """
        if cpu_number == 0:
            search_text = 'Package id 0:'
            field_number = 4
        else:
            search_text = f'Core {cpu_number}:'
            field_number = 3
        return self.exec("sensors | awk '/%s/{print int($%d)}'"
                         % (search_text, field_number),
                         interval=check_interval) + ' C'

    @staticmethod
    def cpu_frequency() -> str:
        """
        Inject CPU frequency as GHz (${freq_g}).

        :return: output string
        """
        return '${freq_g} GHz'

    @staticmethod
    def cpu_top_name(top_number: int) -> str:
        """
        Inject top CPU usage process name by number (${top name...}).

        :param top_number: top number 1-n
        :return: output string
        """
        return '${top name %d}' % top_number

    @staticmethod
    def cpu_top_percent(top_number: int) -> str:
        """
        Inject top CPU usage percent by number (${top cpu...}).

        :param top_number: top number 1-n
        :return: output string
        """
        return '${top cpu %d}%%' % top_number

    def cpu_meter(self,
                  cpu_number: int,
                  width: int = None,
                  height: int = None,
                  graph_color1: str = None,
                  graph_color2: str = None,
                  border_color: str = None,
                  ) -> str:
        """
        Inject CPU meter (${cpugraph...}).

        :param cpu_number: CPU number
        :param width: optional graph width
        :param height: optional graph height
        :param graph_color1: optional graph gradient color #1
        :param graph_color2: optional graph gradient color #2
        :param border_color: optional border color
        :return: output string
        """
        return self.meter('cpugraph',
                          width=width,
                          height=height,
                          param=f'cpu{cpu_number}',
                          graph_color1=graph_color1,
                          graph_color2=graph_color2,
                          border_color=border_color)

    @staticmethod
    def memory_used() -> str:
        """
        Inject memory used.

        :return: output string
        """
        return '${mem}'

    @staticmethod
    def memory_maximum() -> str:
        """
        Inject maximum memory available.

        :return: output string
        """
        return '${memmax}'

    @staticmethod
    def memory_percent() -> str:
        """
        Inject memory percent used.

        :return: output string
        """
        return '${memperc}%'

    @staticmethod
    def memory_usage_triplet() -> str:
        """
        Inject slash-separated memory (used, maximum, percent) triplet.

        :return: output string
        """
        return '${mem} / ${memmax} / ${memperc}%'

    @staticmethod
    def memory_top_name(top_number: int) -> str:
        """
        Inject top memory usage process name by number (${top_mem name...}).

        :param top_number: top number 1-n
        :return: output string
        """
        return '${top_mem name %d}' % top_number

    @staticmethod
    def memory_top_percent(top_number: int) -> str:
        """
        Inject top memory usage percent by number (${top_mem mem...}).

        :param top_number: top number 1-n
        :return: output string
        """
        return '${top_mem mem %d}%%' % top_number

    def memory_bar(self,
                   width: int = None,
                   height: int = None,
                   color: str = None,
                   ) -> str:
        """
        Inject memory usage bar (${membar...}).

        :param width: optional width
        :param height: optional height
        :param color: optional color
        :return: output string
        """
        return self.bar('membar', width=width, height=height, color=color)

    @staticmethod
    def swap_used() -> str:
        """
        Inject swap space used.

        :return: output string
        """
        return '${swap}'

    @staticmethod
    def swap_maximum() -> str:
        """
        Inject maximum swap space available.

        :return: output string
        """
        return '${swapmax}'

    @staticmethod
    def swap_percent() -> str:
        """
        Inject swap space percent used.

        :return: output string
        """
        return '${swapperc}%'

    @staticmethod
    def swap_usage_triplet() -> str:
        """
        Inject slash-separated swap space (used, maximum, percent) triplet.

        :return: output string
        """
        return '${swap} / ${swapmax} / ${swapperc}%'

    @staticmethod
    def filesystem_used(mountpoint: str) -> str:
        """
        Inject filesystem space used by mountpoint.

        :param mountpoint: mountpoint path
        :return: output string
        """
        return '${fs_used %s}' % mountpoint

    @staticmethod
    def filesystem_maximum(mountpoint: str) -> str:
        """
        Inject maximum available space filesystem by mountpoint.

        :param mountpoint: mountpoint path
        :return: output string
        """
        return '${fs_size %s}' % mountpoint

    @staticmethod
    def filesystem_percent(mountpoint: str) -> str:
        """
        Inject filesystem space percent used by mountpoint.

        :param mountpoint: mountpoint path
        :return: output string
        """
        return '${fs_used_perc %s}%%' % mountpoint

    @staticmethod
    def filesystem_usage_triplet(mountpoint: str) -> str:
        """
        Inject slash-separated filesystem (used, maximum, percent) triplet by mountpoint.

        :param mountpoint: mountpoint path
        :return: output string
        """
        return (f'${{fs_used {mountpoint}}}'
                f' / ${{fs_size {mountpoint}}}'
                f' / ${{fs_used_perc {mountpoint}}}%')

    @staticmethod
    def filesystem_io(mountpoint: str) -> str:
        """
        Inject filesystem I/O amount by mountpoint.

        :param mountpoint: mountpoint path
        :return: output string
        """
        return '${diskio %s}' % mountpoint

    def filesystem_bar(self,
                       mountpoint: str,
                       color: str = None,
                       width: int = None,
                       height: int = None,
                       ) -> str:
        """
        Inject filesystem usage bar (${fs_bar...}) by mountpoint.

        :param mountpoint: mountpoint path
        :param color: optional color spec
        :param width: optional width
        :param height: optional height
        :return: output string
        """
        return self.bar('fs_bar', width=width, height=height, color=color, param=mountpoint)

    def filesystem_io_meter(self,
                            device: str,
                            width: int = None,
                            height: int = None,
                            graph_color1: str = None,
                            graph_color2: str = None,
                            border_color: str = None,
                            ) -> str:
        """
        Inject filesystem usage bar (${diskiograph...}) by device name.

        :param device: filesystem device name
        :param width: optional graph width
        :param height: optional graph height
        :param graph_color1: optional graph gradient color #1
        :param graph_color2: optional graph gradient color #2
        :param border_color: optional border color
        :return: output string
        """
        return self.meter('diskiograph',
                          width=width,
                          height=height,
                          graph_color1=graph_color1,
                          graph_color2=graph_color2,
                          border_color=border_color,
                          param=device)


def _generate(conky: ConkyMaker) -> str:
    sections: List[str] = []
    config_lines: List[str] = ['conky.config = {']
    config_dict = dict(
        BASE_CONFIGURATION,
        alignment=conky.placement,
        border_outer_margin=conky.window_outer_margin,
        default_color=conky.default_color,
        default_outline_color=conky.default_color_outline,
        font=conky.default_font,
        gap_x=conky.window_gap,
        gap_y=conky.window_gap,
        update_interval=conky.refresh_interval,
        minimum_width=conky.window_width_min,
        minimum_height=conky.window_height_min,
    )
    config_item_count = 0
    for name, value in config_dict.items():
        if config_item_count > 0:
            config_lines[-1] += ','
        if isinstance(value, str):
            value_string = f"'{value}'"
        elif isinstance(value, bool):
            value_string = str(value).lower()
        else:
            value_string = str(value)
        config_lines.append(f'    {name} = {value_string}')
        config_item_count += 1
    config_lines.append('}')
    sections.append(
        os.linesep.join(config_lines)
    )
    sections.append(
        os.linesep.join([
            'conky.text = [[',
            os.linesep.join(conky.lines),
            ']]',
        ])
    )
    return (os.linesep * 2).join(sections)


def main():
    """Parse command line, load files, and generate Conky output."""

    # Make this file's classes accessible through a module named "conky".
    module_spec = spec_from_file_location('conky', __file__)
    module = module_from_spec(module_spec)
    sys.modules['conky'] = module
    module_spec.loader.exec_module(module)

    # Parse the command line.
    parser = argparse.ArgumentParser(description='Conky configuration generator')
    parser.add_argument(dest='DATA_PATH', help='maker data file path')
    parser.add_argument(dest='DESIGN_PATH', help='maker design file path')
    args = parser.parse_args()
    if not os.path.isfile(args.DATA_PATH):
        abort(f'Configuration path is not a file: {args.DATA_PATH}')
    if not os.path.isfile(args.DESIGN_PATH):
        abort(f'Design path is not a file: {args.DESIGN_PATH}')

    # Load the configuration (as YAML or JSON).
    try:
        extension = os.path.splitext(args.DATA_PATH)[1]
        is_yaml: Optional[bool] = None
        if extension.lower() in ('.yaml', '.yml'):
            is_yaml = True
        if extension.lower() == '.json':
            is_yaml = False
        with open(args.DATA_PATH, encoding='utf-8') as stream:
            configuration_text = stream.read()
            if is_yaml is None:
                is_yaml = not configuration_text.lstrip().startswith('{')
            if is_yaml:
                # noinspection PyUnresolvedReferences
                import yaml
                parameters_dict = yaml.safe_load(configuration_text)
            else:
                # noinspection PyUnresolvedReferences
                import json
                parameters_dict = json.loads(configuration_text)
            parameters = ConfigDict(parameters_dict)
    except (IOError, OSError) as exc:
        abort(f'Failed to load instance configuration: {exc}')

    # Load the design.
    module_spec = spec_from_file_location('design', args.DESIGN_PATH)
    design_module = module_from_spec(module_spec)
    module_spec.loader.exec_module(design_module)

    # Render the conky configuration text.
    maker_class = getattr(design_module, 'Maker', None)
    if maker_class is None:
        abort(f'Design module has no ConkyMaker subclass named "Maker":'
              f' {args.DESIGN_PATH}')
    conky = maker_class(parameters)
    conky.configure_conky(placement=parameters.geometry.placement,
                          window_width_min=parameters.geometry.width_min,
                          window_height_min=parameters.geometry.height_min,
                          window_outer_margin=parameters.geometry.outer_margin,
                          window_gap=parameters.geometry.gap)
    conky.render()

    print(_generate(conky))


if __name__ == '__main__':
    main()
