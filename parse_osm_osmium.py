#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
import csv
import geojson
import xml.etree.ElementTree as ET
from typing import Dict, List, Any

def parse_osm_with_elementtree(osm_file: str) -> Dict[str, Any]:
    """使用ElementTree解析OSM文件，提取节点和道路数据"""
    tree = ET.parse(osm_file)
    root = tree.getroot()

    # 提取所有节点坐标
    nodes = {}
    for elem in root:
        if elem.tag == 'node':
            nodes[elem.attrib['id']] = {
                'lat': float(elem.attrib['lat']),
                'lon': float(elem.attrib['lon'])
            }

    # 提取所有道路及其属性
    ways = []
    for elem in root:
        if elem.tag == 'way':
            tags = {tag.attrib['k']: tag.attrib['v'] for tag in elem.findall('tag')}
            if 'highway' in tags:  # 仅处理道路数据
                ways.append({
                    'id': elem.attrib['id'],
                    'nodes': [nd.attrib['ref'] for nd in elem.findall('nd')],
                    'tags': tags
                })

    return {'nodes': nodes, 'ways': ways}

def filter_lane_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """过滤含车道信息的道路数据"""
    laned_ways = []
    for way in data['ways']:
        if 'lanes' in way['tags'] and way['tags']['highway'] in [
            'motorway', 'trunk', 'primary', 'secondary'
        ]:
            # 关联节点坐标
            coordinates = []
            for node_id in way['nodes']:
                if node_id in data['nodes']:
                    coordinates.append({
                        'lat': data['nodes'][node_id]['lat'],
                        'lon': data['nodes'][node_id]['lon']
                    })

            laned_ways.append({
                'id': way['id'],
                'lanes': way['tags']['lanes'],
                'road_type': way['tags']['highway'],
                'coordinates': coordinates
            })

    return laned_ways

def save_to_csv(data: List[Dict[str, Any]], output_file: str):
    """将车道数据保存为CSV"""
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Way ID', 'Lanes', 'Road Type', 'Node Count'])
        for way in data:
            writer.writerow([
                way['id'],
                way['lanes'],
                way['road_type'],
                len(way['coordinates'])
            ])

def save_to_geojson(data: List[Dict[str, Any]], output_file: str):
    """将车道数据保存为GeoJSON"""
    features = []
    for way in data:
        if len(way['coordinates']) >= 2:  # 至少需要两个点构成线
            line = geojson.LineString([
                (coord['lon'], coord['lat']) for coord in way['coordinates']
            ])
            features.append(geojson.Feature(
                geometry=line,
                properties={
                    'id': way['id'],
                    'lanes': way['lanes'],
                    'road_type': way['road_type']
                }
            ))

    with open(output_file, 'w', encoding='utf-8') as f:
        geojson.dump(geojson.FeatureCollection(features), f)

def main():
    # 输入输出文件配置
    input_osm_file = 'map.osm'       # 替换为你的OSM文件路径
    output_csv_file = 'roads.csv'    # CSV输出路径
    output_geojson_file = 'roads.geojson'  # GeoJSON输出路径

    # 1. 解析OSM数据
    print(f"正在解析OSM文件: {input_osm_file}...")
    osm_data = parse_osm_with_elementtree(input_osm_file)

    # 2. 提取车道信息
    print("正在提取车道数据...")
    lane_data = filter_lane_data(osm_data)

    # 3. 保存结果
    print(f"保存CSV到: {output_csv_file}")
    save_to_csv(lane_data, output_csv_file)

    print(f"保存GeoJSON到: {output_geojson_file}")
    save_to_geojson(lane_data, output_geojson_file)

    print(f"完成！共处理 {len(lane_data)} 条车道数据")

if __name__ == '__main__':
    main()

# !/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
import csv
import geojson
import xml.etree.ElementTree as ET
from typing import Dict, List, Any
import numpy as np


def parse_osm(osm_file: str) -> Dict[str, Any]:
    """解析OSM文件，提取节点、道路、边界和属性"""
    tree = ET.parse(osm_file)
    root = tree.getroot()

    data = {'nodes': {}, 'ways': [], 'boundaries': []}

    # 提取所有节点
    for elem in root:
        if elem.tag == 'node':
            data['nodes'][elem.attrib['id']] = {
                'lat': float(elem.attrib['lat']),
                'lon': float(elem.attrib['lon']),
                'tags': {tag.attrib['k']: tag.attrib['v'] for tag in elem.findall('tag')}
            }

    # 提取所有道路（含属性）和边界（如车道边线）
    for elem in root:
        if elem.tag == 'way':
            tags = {tag.attrib['k']: tag.attrib['v'] for tag in elem.findall('tag')}
            way_type = 'road' if 'highway' in tags else 'boundary' if 'boundary' in tags else 'other'

            # 关联节点坐标
            coordinates = []
            for nd in elem.findall('nd'):
                node_id = nd.attrib['ref']

                if node_id in data['nodes']:
                    coordinates.append({
                        'lat': data['nodes'][node_id]['lat'],
                        'lon': data['nodes'][node_id]['lon']
                    })

            entry = {
                'id': elem.attrib['id'],
                'type': way_type,
                'tags': tags,
                'coordinates': coordinates
            }

            if way_type == 'road':
                data['ways'].append(entry)
            elif way_type == 'boundary':
                data['boundaries'].append(entry)

    return data


def calculate_centerline(coordinates: List[Dict]) -> Dict[str, float]:
    """计算道路中心线（坐标均值）"""
    if not coordinates:
        return None
    lats = np.array([c['lat'] for c in coordinates])
    lons = np.array([c['lon'] for c in coordinates])
    return {
        'center_lat': np.mean(lats),
        'center_lon': np.mean(lons)
    }


def process_roads(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """处理道路数据，提取中心线、边线等信息"""
    processed = []
    for way in data['ways']:
        # 中心线坐标
        center = calculate_centerline(way['coordinates'])
        # 边线信息（首尾点）
        left_edge = way['coordinates'][0] if way['coordinates'] else None
        right_edge = way['coordinates'][-1] if way['coordinates'] else None

        processed.append({
            'id': way['id'],
            'road_type': way['tags'].get('highway', 'unknown'),
            'lanes': way['tags'].get('lanes', 'N/A'),
            'name': way['tags'].get('name', 'unnamed'),
            'center_lat': center['center_lat'] if center else None,
            'center_lon': center['center_lon'] if center else None,
            'left_edge': left_edge,
            'right_edge': right_edge,
            'node_count': len(way['coordinates'])
        })
    return processed


def save_to_csv(data: List[Dict[str, Any]], output_file: str):
    """保存道路数据到CSV"""
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Way ID', 'Road Type', 'Lanes', 'Name',
            'Center Lat', 'Center Lon',
            'Left Edge Lat', 'Left Edge Lon',
            'Right Edge Lat', 'Right Edge Lon',
            'Node Count'
        ])
        for road in data:
            writer.writerow([
                road['id'],
                road['road_type'],
                road['lanes'],
                road['name'],
                road['center_lat'],
                road['center_lon'],
                road['left_edge']['lat'] if road['left_edge'] else '',
                road['left_edge']['lon'] if road['left_edge'] else '',
                road['right_edge']['lat'] if road['right_edge'] else '',
                road['right_edge']['lon'] if road['right_edge'] else '',
                road['node_count']
            ])


def save_to_geojson(data: List[Dict[str, Any]], output_file: str):
    """保存道路中心线和边线到GeoJSON"""
    features = []
    for road in data:
        if road['center_lat'] and road['center_lon']:
            # 中心线点
            center_point = geojson.Point((road['center_lon'], road['center_lat']))
            features.append(geojson.Feature(
                geometry=center_point,
                properties={
                    'id': road['id'],
                    'type': 'center',
                    'road_type': road['road_type']
                }
            ))
        # 边线（首尾点连线）
        if road['left_edge'] and road['right_edge']:
            line = geojson.LineString([
                (road['left_edge']['lon'], road['left_edge']['lat']),
                (road['right_edge']['lon'], road['right_edge']['lat'])
            ])
            features.append(geojson.Feature(
                geometry=line,
                properties={
                    'id': road['id'],
                    'type': 'edge',
                    'road_type': road['road_type']
                }
            ))

    with open(output_file, 'w', encoding='utf-8') as f:
        geojson.dump(geojson.FeatureCollection(features), f)


def main():
    input_osm_file = r'D:\移动的C盘的桌面文件\xiamen0422.osm'  # 输入OSM文件
    output_csv_file = 'roads.csv'  # CSV输出路径
    output_geojson_file = 'roads.geojson'  # GeoJSON输出路径

    # 1. 解析OSM数据
    print(f"解析OSM文件: {input_osm_file}...")
    osm_data = parse_osm(input_osm_file)

    # 2. 处理道路信息
    print("提取道路中心线和边线...")
    processed_roads = process_roads(osm_data)

    # 3. 保存结果
    print(f"保存CSV到: {output_csv_file}")
    save_to_csv(processed_roads, output_csv_file)

    print(f"保存GeoJSON到: {output_geojson_file}")
    save_to_geojson(processed_roads, output_geojson_file)

    print(f"完成！共处理 {len(processed_roads)} 条道路")


if __name__ == '__main__':
    main()