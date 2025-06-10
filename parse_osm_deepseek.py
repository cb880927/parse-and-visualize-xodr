import xml.etree.ElementTree as ET
import csv
import json


def main(input_osm_path):
    # 解析OSM文件
    tree = ET.parse(input_osm_path)
    root = tree.getroot()

    # 存储节点坐标
    nodes = {}
    for node in root.findall('node'):
        nodes[node.attrib['id']] = (
            node.attrib['lon'],
            node.attrib['lat']
        )

    # 保存节点到CSV
    with open('nodes.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['node_id', 'lon', 'lat'])
        for nid, coord in nodes.items():
            writer.writerow([nid, coord[0], coord[1]])

    # 处理所有路径（边）
    with open('edges.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['way_id', 'tags', 'node_ids'])

        for way in root.findall('way'):
            way_id = way.attrib['id']
            tags = {tag.attrib['k']: tag.attrib['v']
                    for tag in way.findall('tag')}
            node_ids = [nd.attrib['ref'] for nd in way.findall('nd')]

            writer.writerow([
                way_id,
                json.dumps(tags, ensure_ascii=False),
                ','.join(node_ids)
            ])

    # 提取道路信息（含highway标签的路径）
    roads = []
    for way in root.findall('way'):
        tags = {tag.attrib['k']: tag.attrib['v']
                for tag in way.findall('tag')}
        if 'highway' in tags:# 不同的项目需要观察不同的字段。
            roads.append({
                'id': way.attrib['id'],
                'name': tags.get('name', ''),
                'type': tags['highway'],
                'nodes': [nd.attrib['ref'] for nd in way.findall('nd')]
            })

    # 保存道路信息
    with open('roads_1.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['road_id', 'name', 'type', 'node_count'])
        for road in roads:
            writer.writerow([
                road['id'],
                road['name'],
                road['type'],
                len(road['nodes'])
            ])

    # 生成道路中心线坐标
    with open('road_centerlines.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['road_id', 'point_num', 'lon', 'lat'])

        for road in roads:
            road_id = road['id']
            for idx, nid in enumerate(road['nodes']):
                if nid in nodes:
                    writer.writerow([
                        road_id,
                        idx,
                        nodes[nid][0],
                        nodes[nid][1]
                    ])
                else:
                    print(f'警告：缺失节点{nid}，道路{road_id}')


if __name__ == '__main__':
    input_file = r'D:\移动的C盘的桌面文件\xiamen0422.osm'  # 修改为你的OSM文件路径
    main(input_file)