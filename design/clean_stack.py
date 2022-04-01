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

from conky import ConfigDict, ConkyFormatter, ConkyFormatterParameters


def render(parameters: ConfigDict, conky: ConkyFormatter):

    conky.set_parameters(
        ConkyFormatterParameters(
            color_default='404040',
            color_outline='808080',
            color_graph_border='404040',
            color_heading='80c0c0',
            color_label='b0b080',
            color_data='f0f0a0',
            color_time='a00000',
            color_date='a07000',
            color_cpu='a0a000',
            color_memory='008000',
            color_filesystem='006060',
            font_default='Montserrat:size=10',
            font_heading='Montserrat:size=11',
            font_label='Montserrat:size=9',
            font_data='MesloLGS NF-Bold:size=9',
            font_time='MesloLGS NF-Bold:size=44',
            font_date='Montserrat:size=14',
            format_time='%H:%M',
            format_date='%a %d %b %Y',
        )
    )

    conky.block(
        conky.time_line(),
        '',
        conky.date_line(),
    )

    conky.block(
        conky.name_value_line('Host:', conky.host_name()),
        conky.name_value_line('Kernel:', conky.kernel()),
        conky.name_value_line('Uptime:', conky.uptime(short=True)),
        conky.name_value_line('External IP:', conky.external_ip()),
        heading='SYSTEM',
    )

    for network in parameters.networks:
        conky.block(
            conky.name_value_line(conky.mac_address(network.device),
                                  conky.ip_address(network.device)),
            heading=f'NET: {network.device}',
        )

    for cpu in parameters.cpus:
        conky.block(
            conky.centered_line(conky.cpu_meter(cpu.cpu_number)),
            conky.triplet_line(conky.cpu_percent(cpu.cpu_number),
                               conky.cpu_frequency(),
                               conky.cpu_temperature(cpu.cpu_number)),
            heading=f'CPU: {cpu.label}',
        )

    conky.block(
        conky.centered_line(conky.memory_bar()),
        conky.name_value_line('Usage:', conky.memory_usage()),
        conky.name_value_line('Swap:', conky.swap_usage()),
        heading='MEMORY',
    )

    for fs in parameters.filesystems:
        conky.block(
            conky.centered_line(conky.filesystem_bar(fs.mountpoint)),
            conky.name_value_line('Usage:', conky.filesystem_usage(fs.mountpoint)),
            conky.centered_line(conky.filesystem_io_meter(fs.device)),
            conky.name_value_line('I/O:', conky.filesystem_io(fs.mountpoint)),
            heading=f'FS: {fs.mountpoint}',
        )

    conky.block(
        [
            conky.name_value_line(conky.cpu_top_name(top_number),
                                  conky.cpu_top_percent(top_number))
            for top_number in range(1, parameters.cpu_top_processes + 1)
        ],
        heading='TOP: CPU',
    )

    conky.block(
        [
            conky.name_value_line(conky.memory_top_name(top_number),
                                  conky.memory_top_percent(top_number))
            for top_number in range(1, parameters.memory_top_processes + 1)
        ],
        heading='TOP: MEMORY',
    )
