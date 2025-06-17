import xml.etree.ElementTree as ET
import pandas as pd
import os
import math
import numpy as np


def parse_osm_file(osm_file_path):
    # 解析XML文件
    tree = ET.parse(osm_file_path)
    root = tree.getroot()

    # 存储数据的容器
    nodes = []
    ways = []
    relations = []

    # 解析所有节点
    for node in root.findall('node'):
        # 提取单个节点信息，包括ID、动作、经纬度及标签
        node_id = node.get('id')
        action = node.get('action', default='')
        lat = node.get('lat')
        lon = node.get('lon')
        tags = {}

        for tag in node.findall('tag'):
            tags[tag.get('k')] = tag.get('v')

        nodes.append({
            'id': node_id,
            'action': action,
            'lat': lat,
            'lon': lon,
            **tags
        })

    # 解析所有路径
    for way in root.findall('way'):
        # 提取单条路径信息，包括ID、动作、可见性、版本、引用节点及标签
        way_id = way.get('id')
        action = way.get('action', '')
        visible = way.get('visible', '')
        version = way.get('version', '')

        # 获取节点引用
        node_refs = [nd.get('ref') for nd in way.findall('nd')]

        # 获取标签
        tags = {}
        for tag in way.findall('tag'):
            tags[tag.get('k')] = tag.get('v')

        ways.append({
            'id': way_id,
            'action': action,
            'visible': visible,
            'version': version,
            'node_refs': ','.join(node_refs),
            'node_count': len(node_refs),
            **tags
        })

    # 解析所有关系
    for relation in root.findall('relation'):
        # 提取单个关系信息，包括ID、动作、可见性、成员及标签
        rel_id = relation.get('id')
        action = relation.get('action', '')
        visible = relation.get('visible', '')

        # 获取成员
        members = []
        for member in relation.findall('member'):
            members.append(f"{member.get('type')}/{member.get('ref')}/{member.get('role')}")

        # 获取标签
        tags = {}
        for tag in relation.findall('tag'):
            tags[tag.get('k')] = tag.get('v')

        relations.append({
            'id': rel_id,
            'action': action,
            'visible': visible,
            'members': ';'.join(members),
            **tags
        })

    return nodes, ways, relations


def save_to_csv(data, filename):
    # 将解析的数据保存为CSV文件
    if data:
        df = pd.DataFrame(data)

        # 在 node_refs 前添加单引号，确保 Excel 等工具识别为文本
        if 'node_refs' in df.columns:
            df['node_refs'] = "'" + df['node_refs'].astype(str)

        df.to_csv(filename, index=False)
        print(f"Saved {len(df)} records to {filename}")
    else:
        print(f"No data to save for {filename}")


def find_nodes_by_id(nodes, node_id):
    # 根据节点ID查找对应的节点信息
    for node in nodes:
        if node['id'] == node_id:
            return node
    return None


def find_ways_by_id(ways, way_id):
    # 根据路径ID查找对应的路径信息
    for way in ways:
        if way['id'] == way_id:
            return way
    return None


# 计算箭头线角度
def calc_arrow_angles(x1, y1, x2, y2, alpha=10):
    # 计算基础角度
    dx = float(x2) - float(x1)
    dy = float(y2) - float(y1)
    base_angle = math.atan2(dy, dx)  # [-π, π]

    # 计算反方向角度（度）
    reverse_angle = math.degrees(base_angle) + 180

    # 计算箭头线角度
    angle1 = (reverse_angle + alpha) % 360
    angle2 = (reverse_angle - alpha) % 360

    return round(angle1, 2), round(angle2, 2)


def save_to_scr(nodes, ways, relations):
    # 将解析结果保存为SCR脚本文件，用于CAD绘制图形
    open_file_nodes = open(r'osm_data_output\nodes.scr', mode='w')
    open_file_ways = open(r'osm_data_output\ways.scr', mode='w')
    open_file_relations = open(r'osm_data_output\relations.scr', mode='w')

    # 过滤已删除的节点
    for node in nodes[:]:  # 遍历列表的副本，把已经删除的点给去掉。
        if node['action'] == 'delete':
            nodes.remove(node)

    # 画点，用圆形,蓝色
    open_file_nodes.write(f"color 5\n")
    for node in nodes:
        coord_x = node['local_x']
        coord_y = node['local_y']
        open_file_nodes.write(f"circle {coord_x},{coord_y} 0.2 \n")

    # 过滤已删除的路径
    for way in ways[:]:  # 遍历列表的副本，把已经删除的边给去掉。
        if way['action'] == 'delete' or int(way['id']) < 0:
            ways.remove(way)

    # 画线，白色
    open_file_ways.write(f"color 7\n")
    for j in range(len(ways)):
        way_nodes = ways[j]['node_refs'].split(",")
        if way_nodes == '':
            continue
        for i in range(len(way_nodes) - 1):
            node_1 = find_nodes_by_id(nodes, way_nodes[i])
            node_2 = find_nodes_by_id(nodes, way_nodes[i + 1])
            coord_x_1 = node_1['local_x']
            coord_y_1 = node_1['local_y']
            coord_x_2 = node_2['local_x']
            coord_y_2 = node_2['local_y']
            open_file_ways.write(f"line {coord_x_1},{coord_y_1} {coord_x_2},{coord_y_2} \n")
            # 在way的尾部画箭头
            if i == len(way_nodes) - 2:
                angle1, angle2 = calc_arrow_angles(coord_x_1, coord_y_1, coord_x_2, coord_y_2)
                open_file_ways.write(f"line {coord_x_2},{coord_y_2} @0.5<{angle1} \n")
                open_file_ways.write(f"line {coord_x_2},{coord_y_2} @0.5<{angle2} \n")

    # 绘制车道流向
    open_file_relations.write(f"color 10\n")
    for relation in relations[:]:
        if relation['action'] == 'delete' or float(relation['id']) < 0:
            continue
        from_way = find_ways_by_id(ways, relation['members'].split(";")[0].split("/")[1])
        to_way = find_ways_by_id(ways, relation['members'].split(";")[1].split("/")[1])

        if from_way is None or to_way is None:
            continue
        #  判断way的role，用以判断方向，并将from_way和to_way交换位置。
        if relation['members'].split(";")[0].split("/")[2] == 'right':
            temp = from_way
            from_way = to_way
            to_way = temp
        from_node_1 = find_nodes_by_id(nodes, from_way['node_refs'].split(",")[0])
        from_node_2 = find_nodes_by_id(nodes, from_way['node_refs'].split(",")[1])
        to_node_1 = find_nodes_by_id(nodes, to_way['node_refs'].split(",")[0])
        to_node_2 = find_nodes_by_id(nodes, to_way['node_refs'].split(",")[1])
        from_vector = [float(from_node_2['local_x']) - float(from_node_1['local_x']),
                       float(from_node_2['local_y']) - float(from_node_1['local_y'])]
        to_vector = [float(to_node_2['local_x']) - float(to_node_1['local_x']),
                     float(to_node_2['local_y']) - float(to_node_1['local_y'])]

        # 车道流向是和role为left的way的点一致的。
        if (from_vector[0] * to_vector[0] + from_vector[1] * to_vector[1]) < 0:  # 判断两个向量的叉积是否为正，如果为正，则两个向量方向一致。
            to_way['node_refs'] = ','.join(to_way['node_refs'].split(",")[::-1])

        # 根据from_way中的点，以及根据from_way和to_way中的点计算出来的便宜，画出车道方向
        # 先计算车道线的长度。
        lane_length, arrow_gap = 0, 5  # 箭头间隔，可配置数据。
        # 长短不相等，则跳过。
        if len(from_way['node_refs'].split(",")) != len(to_way['node_refs'].split(",")):
            continue

        for i in range(len(from_way['node_refs'].split(",")) - 2):
            node_1 = find_nodes_by_id(nodes, from_way['node_refs'].split(",")[i])
            node_2 = find_nodes_by_id(nodes, to_way['node_refs'].split(",")[i])
            coord_x_1 = float(node_1['local_x'])
            coord_y_1 = float(node_1['local_y'])
            coord_x_2 = float(node_2['local_x'])
            coord_y_2 = float(node_2['local_y'])
            #  计算车道线长度
            lane_length = lane_length + math.sqrt((coord_x_2 - coord_x_1) ** 2 + (coord_y_2 - coord_y_1) ** 2)
            if lane_length > arrow_gap:
                # 画出车道方向
                angle1, angle2 = [np.mod(angle + 90, 360) for angle in
                                  calc_arrow_angles(coord_x_1, coord_y_1, coord_x_2, coord_y_2)]
                open_file_relations.write(
                    f"line {(coord_x_1 + coord_x_2) / 2},{(coord_y_1 + coord_y_2) / 2} @0.5<{angle1} \n")
                open_file_relations.write(
                    f"line {(coord_x_1 + coord_x_2) / 2},{(coord_y_1 + coord_y_2) / 2} @0.5<{angle2} \n")

    open_file_nodes.flush()
    open_file_nodes.close()

    open_file_ways.flush()
    open_file_ways.close()

    open_file_relations.flush()
    open_file_relations.close()


def get_ways_links(nodes, ways, relations):
    # 获取路径之间的连接关系，用于表示道路之间的连接
    links = []
    for lane_1 in relations:
        #  获取关系转向方向，默认为straight，需要过滤
        from_turn_direction = []
        if 'turn_direction' in lane_1:
            from_turn_direction = lane_1['turn_direction']
        # 过滤掉非道路关系
        if 'subtype' in lane_1:
            lane_1_subtype = lane_1['subtype']
            if lane_1_subtype != 'road':
                continue
        # 遍历所有lane，获取相连的lane
        # 获取关系成员，这一项没有空值，不需要过滤
        members = lane_1['members'].split(";")
        # 第一个member和第二个member是way属性，后续的都不是，得出的结果是member = [['1000','left'],['1001','right']]
        member_lane_1 = [[member.split("/")[1], member.split("/")[2]] for member in members if
                         member.split("/")[0] == 'way']
        for lane_2 in relations:
            if lane_2['id'] == lane_1['id']:  # 两条线相同，跳过
                continue
            #  获取关系转向方向，默认为straight，需要过滤
            to_turn_direction = []
            if 'turn_direction' in lane_2:
                to_turn_direction = lane_2['turn_direction']
            # 过滤掉非道路关系
            if 'subtype' in lane_2:
                lane_2_subtype = lane_2['subtype']
                if lane_2_subtype != 'road':
                    continue

            # 获取关系成员，这一项没有空值，不需要过滤
            members = lane_2['members'].split(";")
            # 这个地方直接写死，应该就第一个member和第二个member是way属性，后续的都不是，得出的结果是member = [['1000','left'],['1001','right']]
            member_lane_2 = [[member.split("/")[1], member.split("/")[2]] for member in members if
                             member.split("/")[0] == 'way']
            # 车道线左右的描述需要一致才会连接，不一致则说明流向相反，不会链接。暂时只考虑流向完全一致的。
            if member_lane_1[0][1] != member_lane_2[0][1]:
                continue
            if find_ways_by_id(ways, member_lane_1[0][0])['node_refs'].split(",")[-1] == \
                    find_ways_by_id(ways, member_lane_2[0][0])['node_refs'].split(",")[0] and \
                    find_ways_by_id(ways, member_lane_1[1][0])['node_refs'].split(",")[-1] == \
                    find_ways_by_id(ways, member_lane_2[1][0])['node_refs'].split(",")[0]:
                # 说明这两个lane是相连接的。
                links.append({
                    'rom_lane_id': lane_1['id'],
                    'to_lane_id': lane_2['id'],
                    'from_turn_direction': from_turn_direction,
                    'to_turn_direction': to_turn_direction,
                    'flow_type': member_lane_1[0][1] + "&" + member_lane_1[1][1]
                })

    return links


def main(osm_file_path):
    # 创建输出目录
    output_dir = "osm_data_output"
    os.makedirs(output_dir, exist_ok=True)

    # 解析OSM文件
    nodes, ways, relations = parse_osm_file(osm_file_path)
    links = get_ways_links(nodes, ways, relations)
    # 输出到cad的scr脚本文件中
    save_to_scr(nodes, ways, relations)

    # 保存到CSV
    save_to_csv(nodes, os.path.join(output_dir, "nodes.csv"))
    save_to_csv(ways, os.path.join(output_dir, "ways.csv"))
    save_to_csv(relations, os.path.join(output_dir, "relations.csv"))
    save_to_csv(links, os.path.join(output_dir, "links.csv"))

    # 打印摘要信息
    print("\nExtraction Summary:")
    print(f"Nodes: {len(nodes)}")
    print(f"Ways: {len(ways)}")
    print(f"Relations: {len(relations)}")
    print(f"\nOutput files saved in: {os.path.abspath(output_dir)}")


if __name__ == "__main__":
    input_file = r"D:\移动的C盘的桌面文件\nanhui0519.osm"  # 替换为你的OSM文件路径
    main(input_file)
