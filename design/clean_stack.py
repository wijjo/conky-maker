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

from typing import Any, List, Union

from conky import ConkyMaker

COLORS = {
    'default': '404040',
    'outline': '808080',
    'graph_border': '404040',
    'heading': '80c0c0',
    'label': 'b0b080',
    'value': 'f0f0a0',
    'time': 'a00000',
    'date': 'a07000',
    'cpu': 'a0a000',
    'memory': '008000',
    'filesystem': '006060',
}

FONTS = {
    'default': 'Montserrat:size=10',
    'heading': 'Montserrat:size=11',
    'label': 'Montserrat:size=9',
    'value': 'MesloLGS NF-Bold:size=9',
    'time': 'MesloLGS NF-Bold:size=44',
    'date': 'Montserrat:size=14',
}

FORMATS = {
    'time': '%H:%M',
    'date': '%a %d %b %Y',
}


class Maker(ConkyMaker):

    meter_height = 25
    bar_height = 10

    def block(self, *items: Union[str, list, tuple], heading: str = None):
        import sys
        sys.stderr.write(f'{heading=}\n')
        if self.lines:
            self.line('')
        if heading is not None:
            heading_text_fields = []
            if heading:
                heading_text_fields.extend([self.font('heading'), heading, ' '])
            self.line(self.color('heading'), *heading_text_fields, self.horizontal_rule())
        for item in items:
            self.line(''.join(item) if isinstance(item, (tuple, list)) else item)

    def label_value_pair(self, label: str, value: Any) -> List[str]:
        return [
            self.color('label'),
            self.font('label'),
            self.text(label),
            self.color('value'),
            self.font('value'),
            self.right(),
            self.text(value),
        ]

    def render(self):

        self.color_theme(COLORS)
        self.font_theme(FONTS)

        self.block(
            (
                self.color('time'),
                self.font('time'),
                self.center(),
                self.time_date(FORMATS['time']),
            ),
            '',
            (
                self.color('date'),
                self.font('date'),
                self.center(),
                self.time_date(FORMATS['date']),
            ),
        )

        self.block(
            self.label_value_pair('Host:', self.host_name()),
            self.label_value_pair('Kernel:', self.kernel()),
            self.label_value_pair('Uptime:', self.uptime(short=True)),
            self.label_value_pair('External IP:', self.external_ip()),
            heading='SYSTEM',
        )

        for network in self.parameters.networks:
            self.block(
                self.label_value_pair(self.mac_address(network.device),
                                      self.ip_address(network.device)),
                heading=f'NET: {network.device}',
            )

        for cpu in self.parameters.cpus:
            self.block(
                (
                    self.center(),
                    self.cpu_meter(cpu.cpu_number,
                                   width=self.parameters.geometry.width_min,
                                   height=self.meter_height,
                                   graph_color1='cpu',
                                   graph_color2='cpu',
                                   border_color='cpu'),
                ),
                (
                    self.color('value'),
                    self.font('value'),
                    self.cpu_percent(cpu.cpu_number),
                    self.center(),
                    self.cpu_frequency(),
                    self.right(),
                    self.cpu_temperature(cpu.cpu_number),
                ),
                heading=f'CPU: {cpu.label}',
            )

        self.block(
            (
                self.center(),
                self.memory_bar(width=self.parameters.geometry.width_min,
                                height=self.bar_height,
                                color='memory'),
            ),
            self.label_value_pair('Usage:', self.memory_usage_triplet()),
            self.label_value_pair('Swap:', self.swap_usage_triplet()),
            heading='MEMORY',
        )

        for fs in self.parameters.filesystems:
            self.block(
                (
                    self.center(),
                    self.filesystem_bar(fs.mountpoint,
                                        width=self.parameters.geometry.width_min,
                                        height=self.bar_height,
                                        color='filesystem',
                                        ),
                ),
                self.label_value_pair('Usage:',
                                      self.filesystem_usage_triplet(fs.mountpoint)),
                (
                    self.center(),
                    self.filesystem_io_meter(fs.device,
                                             width=self.parameters.geometry.width_min,
                                             height=self.meter_height,
                                             graph_color1='filesystem',
                                             graph_color2='filesystem',
                                             border_color='filesystem'),
                ),
                self.label_value_pair('I/O:', self.filesystem_io(fs.mountpoint)),
                heading=f'FS: {fs.mountpoint}',
            )

        self.block(
            *[
                self.label_value_pair(self.cpu_top_name(top_number),
                                      self.cpu_top_percent(top_number))
                for top_number in range(1, self.parameters.processes.top_cpu_count + 1)
            ],
            heading='TOP: CPU',
        )

        self.block(
            *[
                self.label_value_pair(self.memory_top_name(top_number),
                                      self.memory_top_percent(top_number))
                for top_number in range(1, self.parameters.processes.top_memory_count + 1)
            ],
            heading='TOP: MEMORY',
        )
