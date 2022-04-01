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
import dataclasses
from importlib.util import spec_from_file_location, module_from_spec
from typing import Any, List, Union, Tuple, Iterator, Optional

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


def abort(message: Any):
    """
    Display error and exit with error return code.

    :param message: error message to display
    """
    sys.stderr.write(f'ERROR: {message}{os.linesep}')
    sys.exit(1)


def flatten_strings(item: Any) -> Iterator:
    """
    Recursively process a string sequence hierarchy to produce a flat iterable.
    :param item: string item or sequence
    :return: flat string iterator
    """
    if isinstance(item, (list, tuple)):
        for sub_item in item:
            for flattened_sub_item in flatten_strings(sub_item):
                yield flattened_sub_item
    else:
        yield item


# Type for a line string or line string hierarchy.
LinesTree = Union[str, Tuple[str], List[str], Tuple['LinesTree'], List['LinesTree']]

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
        if isinstance(data, dict):
            return cls(data)
        if isinstance(data, list):
            return [cls._wrap_data(item) for item in data]
        return data


@dataclasses.dataclass
class ConkyFormatterParameters:
    """Conky formatter parameters."""
    placement: str = None
    color_default: str = None
    color_outline: str = None
    color_graph_border: str = None
    color_heading: str = None
    color_label: str = None
    color_data: str = None
    color_time: str = None
    color_date: str = None
    color_cpu: str = None
    color_memory: str = None
    color_filesystem: str = None
    font_default: str = None
    font_heading: str = None
    font_label: str = None
    font_data: str = None
    font_time: str = None
    font_date: str = None
    format_time: str = None
    format_date: str = None
    meter_width: int = None
    meter_height: int = None
    bar_width: int = None
    bar_height: int = None
    interval_refresh: int = None
    interval_network_check: int = None
    interval_temperature_check: int = None
    window_width_min: int = None
    window_height_min: int = None
    window_outer_margin: int = None
    window_gap: int = None


# Default formatter parameters.
DEFAULT_FORMATTER_PARAMETERS = ConkyFormatterParameters(
    placement='top_left',
    color_default='000000',
    color_outline='808080',
    color_graph_border='808080',
    color_heading='000000',
    color_label='000000',
    color_data='000000',
    color_time='000000',
    color_date='000000',
    color_cpu='000000',
    color_memory='000000',
    color_filesystem='000000',
    font_default='FreeSans:size=10',
    font_heading='FreeSans:size=11',
    font_label='FreeSans:size=9',
    font_data='FreeMono-Bold:size=9',
    font_time='FreeMono-Bold:size=44',
    font_date='FreeSans:size=14',
    format_time='%H:%M',
    format_date='%c',
    meter_width=100,
    meter_height=30,
    bar_width=100,
    bar_height=10,
    interval_refresh=1,
    interval_network_check=3600,
    interval_temperature_check=600,
    window_width_min=200,
    window_height_min=500,
    window_outer_margin=20,
    window_gap=20,
)


class ConkyFormatter:
    """Conky formatter maps method calls to $xxx Conky macros."""

    def __init__(self, parameters: ConfigDict):
        """
        ConkyFormatter constructor.

        :param parameters: initial parameters to selectively override defaults
        """
        self.parameters = dataclasses.replace(DEFAULT_FORMATTER_PARAMETERS)
        self.set_parameters(
            ConkyFormatterParameters(
                placement=parameters.placement,
                meter_width=parameters.meter_width,
                meter_height=parameters.meter_height,
                bar_width=parameters.bar_width,
                bar_height=parameters.bar_height,
                interval_refresh=parameters.refresh_interval,
                interval_network_check=parameters.network_check_interval,
                interval_temperature_check=parameters.temperature_check_interval,
                window_width_min=parameters.window_width_min,
                window_height_min=parameters.window_height_min,
                window_outer_margin=parameters.window_outer_margin,
                window_gap=parameters.window_gap,
            )
        )
        self.conky_text_lines: List[str] = []

    def set_parameters(self, parameters: ConkyFormatterParameters):
        """
        Selectively override parameters.

        :param parameters: override parameters (the ones that are not None)
        """
        for field in dataclasses.fields(self.parameters):
            value = getattr(parameters, field.name)
            if value is not None:
                setattr(self.parameters, field.name, value)

    @staticmethod
    def text(value: Any) -> str:
        """
        Inject text or other value as string.

        :param value: input value
        :return: output string
        """
        return str(value)

    @staticmethod
    def color(color_spec: Union[str, int] = None) -> str:
        """
        Inject ${color...) to set a color or ${color} to restore default.

        :param color_spec: color number (0-9) or string value, clears color if missing
        :return: output string
        """
        if color_spec is None:
            return '${color}'
        if isinstance(color_spec, int):
            return '${color%d}' % color_spec
        return '${color #%s}' % color_spec

    @staticmethod
    def font(font_spec: str = None) -> str:
        """
        Inject ${font...) to set a font or ${font} to restore default.

        :param font_spec: font specification string - clears font if missing
        :return: output string
        """
        if font_spec is None:
            return '${font}'
        return '${font %s}' % font_spec

    @staticmethod
    def center() -> str:
        """
        Inject centering ($alignc) for subsequent items of current line.

        :return: output string
        """
        return '$alignc'

    @staticmethod
    def right() -> str:
        """
        Inject right-justification ($alignr) for subsequent items of current line.

        :return: output string
        """
        return '$alignr'

    @staticmethod
    def time(time_format: str) -> str:
        """
        Inject time (${time...}).

        :param time_format: strftime-style time format string
        :return: output string
        """
        return '${time %s}' % time_format

    @staticmethod
    def horizontal_rule() -> str:
        """
        Inject horizontal rule ($hr).

        :return: output string
        """
        return '$hr'

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
              color: str,
              width: int,
              height: int,
              param: str = None,
              ) -> str:
        """
        Inject meter (${...graph...}).

        :param graph_type: Conky graph type name, e.g. "cpugraph", "diskiograph"...
        :param color: graph color
        :param width: graph width
        :param height: graph height
        :param param: optional graph parameter (varies by graph type)
        :return: output string
        """
        return '${color #%s}${%s%s %d,%d %s %s}' % (
            self.parameters.color_graph_border,
            graph_type,
            f' {param}' if param else '',
            height, width,
            color, color)

    @staticmethod
    def bar(bar_type: str,
            color: str,
            width: int,
            height: int,
            param: str = None,
            ) -> str:
        """
        Inject horizontal bar meter (${...bar...}).

        :param bar_type: Conky bar type name, e.g. "membar", "fs_bar"...
        :param color: bar color
        :param width: bar width
        :param height: bar height
        :param param: optional bar parameter (varies by bar type)
        :return: output string
        """
        return '${color #%s}${%s %d,%d%s}' % (
            color,
            bar_type,
            height, width,
            f' {param}' if param else '')

    @staticmethod
    def exec(command: str, interval: int = None) -> str:
        """
        Inject output of external command (${exec...} or ${execi...}).

        :param command: external command
        :param interval: optional interval for throttling frequency of expensive command
        :return: output string
        """
        if interval is not None:
            return '${execi %d %s}' % (interval, command)
        return '${exec %s}' % command

    @staticmethod
    def host_name() -> str:
        """
        Inject host name ($nodename).

        :return: output string
        """
        return '$nodename'

    @staticmethod
    def kernel() -> str:
        """
        Inject Linux kernel name ($kernel).

        :return: output string
        """
        return '$kernel'

    @staticmethod
    def uptime(short: bool = False) -> str:
        """
        Inject uptime ($uptime or $uptime_short).

        :param short: provide short form if set and True
        :return: output string
        """
        if short:
            return '$uptime_short'
        return '$uptime'

    @staticmethod
    def ip_address(device: str) -> str:
        """
        Inject IP address of network device (${addr...}).

        :param device: network device name
        :return: output string
        """
        return '${addr %s}' % device

    def mac_address(self, device: str) -> str:
        """
        Inject MAC address of network device.

        Throttled by "interval_network_check" parameter.

        :param device: network device name
        :return: output string
        """
        return self.exec("ip addr show dev %s | awk '/link\\/ether/{print $2}'" % device,
                         interval=self.parameters.interval_network_check)

    def external_ip(self) -> str:
        """
        Inject external IP address.

        Throttled by both the "interval_network_check" parameter and a 4 hour
        cache frequency.

        :return: output string
        """
        return self.exec(f'bash -c "{EXTERNAL_IP_COMMAND}"',
                         interval=self.parameters.interval_network_check)

    @staticmethod
    def cpu_percent(cpu_number: int) -> str:
        """
        Inject CPU usage percent (${cpu cpu...}).

        :param cpu_number: CPU number
        :return: output string
        """
        return '${cpu cpu %s}%%' % cpu_number

    def cpu_temperature(self, cpu_number: int) -> str:
        """
        Inject CPU temperature (Celsius).

        Throttled by "interval_temperature_check" parameter.

        :param cpu_number: CPU number
        :return: output string
        """
        if cpu_number == 0:
            search_text = 'Package id 0:'
            field_number = 4
        else:
            search_text = f'Core {cpu_number}:'
            field_number = 3
        return self.exec("sensors | awk '/%s/{print int($%d)}'" % (search_text, field_number),
                         interval=self.parameters.interval_temperature_check) + ' C'

    @staticmethod
    def cpu_frequency() -> str:
        """
        Inject CPU frequency as GHz ($freq_g).

        :return: output string
        """
        return '$freq_g GHz'

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

    def cpu_meter(self, cpu_number: int) -> str:
        """
        Inject CPU meter (${cpugraph...}).

        Color and size are determined by the "color_cpu", "meter_width", and
        "meter_height" parameters.

        :param cpu_number: CPU number
        :return: output string
        """
        return self.meter('cpugraph',
                          self.parameters.color_cpu,
                          self.parameters.meter_width,
                          self.parameters.meter_height,
                          param=f'cpu{cpu_number}')

    @staticmethod
    def memory_usage() -> str:
        """
        Inject slash-separated memory (used, maximum, percent) triplet.

        :return: output string
        """
        return '$mem / $memmax / $memperc%'

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

    def memory_bar(self) -> str:
        """
        Inject memory usage bar (${membar...}).

        Color and size are determined by the "color_memory", "bar_width", and
        "bar_height" parameters.

        :return: output string
        """
        return self.bar('membar',
                        self.parameters.color_memory,
                        self.parameters.bar_width,
                        self.parameters.bar_height)

    @staticmethod
    def swap_usage() -> str:
        """
        Inject slash-separated swap space (used, maximum, percent) triplet.

        :return: output string
        """
        return '$swap / $swapmax / $swapperc%'

    @staticmethod
    def filesystem_usage(mountpoint: str) -> str:
        """
        Inject slash-separated filesystem (used, maximum, percent) triplet by mountpoint.

        :param mountpoint: mountpoint path
        :return: output string
        """
        return ('${fs_used %(mountpoint)s}'
                ' / ${fs_size %(mountpoint)s}'
                ' / ${fs_used_perc %(mountpoint)s}%%'
                % locals())

    @staticmethod
    def filesystem_io(mountpoint: str) -> str:
        """
        Inject filesystem I/O amount by mountpoint.

        :param mountpoint: mountpoint path
        :return: output string
        """
        return '${diskio %s}' % mountpoint

    def filesystem_bar(self, mountpoint: str) -> str:
        """
        Inject filesystem usage bar (${fs_bar...}) by mountpoint.

        Color and size are determined by the "color_filesystem", "bar_width",
        and "bar_height" parameters.

        :param mountpoint: mountpoint path
        :return: output string
        """
        return self.bar('fs_bar',
                        self.parameters.color_filesystem,
                        self.parameters.bar_width,
                        self.parameters.bar_height,
                        param=mountpoint)

    def filesystem_io_meter(self, device: str) -> str:
        """
        Inject filesystem usage bar (${diskiograph...}) by device name.

        Color and size are determined by the "color_filesystem", "meter_width",
        and "meter_height" parameters.

        :param device: filesystem device name
        :return: output string
        """
        return self.meter('diskiograph',
                          self.parameters.color_filesystem,
                          self.parameters.meter_width,
                          self.parameters.meter_height,
                          param=device)

    @staticmethod
    def line(*parts: str) -> str:
        """
        Inject a full line, including any added macros needed to clear altered color/font.

        :param parts: line parts (strings)
        :return: output string
        """
        changed_color = False
        changed_font = False
        for part in parts:
            for font_color_change in FONT_COLOR_REGEX.finditer(part):
                if font_color_change.group(2) == 'color':
                    changed_color = font_color_change.group(3) not in ('', '}')
                elif font_color_change.group(2) == 'font':
                    changed_font = font_color_change.group(3) not in ('', '}')
        line_parts = list(parts)
        if changed_color:
            line_parts.append('${color}')
        if changed_font:
            line_parts.append('${font}')
        return ''.join(line_parts)

    def time_line(self) -> str:
        """
        Inject a digital clock line.

        Color, font, and format are determined by the "color_time", "font_time",
        and "format_time" parameters.

        :return: output string
        """
        return self.line(
            self.color(self.parameters.color_time),
            self.font(self.parameters.font_time),
            self.center(),
            self.time(self.parameters.format_time),
        )

    def date_line(self) -> str:
        """
        Inject a date line.

        Color, font, and format are determined by the "color_date", "font_date",
        and "format_date" parameters.

        :return: output string
        """
        return self.line(
            self.color(self.parameters.color_date),
            self.font(self.parameters.font_date),
            self.center(),
            self.time(str(self.parameters.format_date)),
        )

    def heading_line(self, heading_text: str) -> str:
        """
        Inject a heading line with trailing horizontal rule.

        Color and font are determined by the "color_heading" and "font_heading"
        parameters.

        :return: output string
        """
        return self.line(
            self.color(self.parameters.color_heading),
            self.font(self.parameters.font_heading),
            self.text(heading_text + ' '),
            self.horizontal_rule(),
        )

    def name_value_line(self, name: Any, value: Any) -> str:
        """
        Inject a name/value pair line.

        Color and font are determined by the "color_label", "color_data",
        "font_label", and "font_data" parameters.

        :param name: name (label)
        :param value: value
        :return: output string
        """
        return self.line(
            self.color(self.parameters.color_label),
            self.font(self.parameters.font_label),
            self.text(name),
            self.color(self.parameters.color_data),
            self.font(self.parameters.font_data),
            self.right(),
            self.text(value),
        )

    def pair_line(self, value1: Any, value2: Any) -> str:
        """
        Inject a data value pair line.

        Color and font are determined by the "color_data" and "font_data"
        parameters.

        :param value1: value #1
        :param value2: value #2
        :return: output string
        """
        return self.line(
            self.color(self.parameters.color_data),
            self.font(self.parameters.font_data),
            self.text(value1),
            self.right(),
            self.text(value2),
        )

    def triplet_line(self, value1: Any, value2: Any, value3: Any) -> str:
        """
        Inject a data value triplet line.

        Color and font are determined by the "color_data" and "font_data"
        parameters.

        :param value1: value #1
        :param value2: value #2
        :param value3: value #3
        :return: output string
        """
        return self.line(
            self.color(self.parameters.color_data),
            self.font(self.parameters.font_data),
            self.text(value1),
            self.center(),
            self.text(value2),
            self.right(),
            self.text(value3),
        )

    @classmethod
    def centered_line(cls, item: Any) -> str:
        """
        Inject a centered line with a single item.

        :param item: data item
        :return: output string
        """
        return cls.line(
            cls.center(),
            cls.text(item),
        )

    def block(self,
              *lines: LinesTree,
              heading: str = None,
              vertical_offset: int = None,
              ):
        """
        Inject a multi-line block with optional heading and vertical offset.

        :param lines: block lines, which are flattened if nested
        :param heading: optional heading
        :param vertical_offset: optional vertical offset
        :return: output string
        """
        if self.conky_text_lines:
            self.conky_text_lines.append('')
        first_line_index = len(self.conky_text_lines)
        # conky.line() appends ${color}/${font} as needed to clear temporary changes.
        if heading is not None:
            self.conky_text_lines.append(self.line(self.heading_line(heading)))
        for flattened_line in flatten_strings(lines):
            self.conky_text_lines.append(self.line(flattened_line))
        if vertical_offset:
            self.conky_text_lines[first_line_index] = ''.join([
                self.offset(y=vertical_offset),
                self.conky_text_lines[first_line_index]
            ])

    def conky_config_section(self) -> str:
        """
        Generate full Conky configuration section block, including wrapper lines.

        :return: output string
        """
        lines: List[str] = []
        config_dict = dict(
            BASE_CONFIGURATION,
            alignment=self.parameters.placement,
            border_outer_margin=self.parameters.window_outer_margin,
            default_color=self.parameters.color_default,
            default_outline_color=self.parameters.color_outline,
            font=self.parameters.font_default,
            gap_x=self.parameters.window_gap,
            gap_y=self.parameters.window_gap,
            update_interval=self.parameters.interval_refresh,
            minimum_width=self.parameters.window_width_min,
            minimum_height=self.parameters.window_height_min,
        )
        lines.append('conky.config = {')
        count = 0
        for name, value in config_dict.items():
            if count > 0:
                lines[-1] += ','
            if isinstance(value, str):
                value_string = f"'{value}'"
            elif isinstance(value, bool):
                value_string = str(value).lower()
            else:
                value_string = str(value)
            lines.append(f'    {name} = {value_string}')
            count += 1
        lines.append('}')
        return os.linesep.join(lines)

    def conky_text_section(self) -> str:
        """
        Generate full Conky text block, including wrapper lines.

        :return: output string
        """
        return os.linesep.join([
            'conky.text = [[',
            *self.conky_text_lines,
            ']]',
        ])

    def generate_conky_configuration(self) -> str:
        """
        Generate full Conky configuration, wrapped configuration and text sections.

        :return: output string
        """
        return (os.linesep * 2).join([
            self.conky_config_section(),
            self.conky_text_section(),
        ])


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
    if not hasattr(design_module, 'render'):
        abort(f'Design module missing render() function: {args.DESIGN_PATH}')

    # Render the conky configuration text.
    formatter = ConkyFormatter(parameters)
    getattr(design_module, 'render')(parameters, formatter)
    print(formatter.generate_conky_configuration())


if __name__ == '__main__':
    main()
