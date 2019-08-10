# NeteaseMusicLottery
网易云音乐动态互动抽奖  / Netease Cloud Music Dynamics Lottery Draw

## 版本
version 0.0.1.0810 beta

## 提示
写着玩、写着玩、写着玩, 代码比较乱，只完成基础功能

## 安装
1. 克隆项目代码
```bash
git clone https://github.com/lkeme/NeteaseMusicLottery.git

cd NeteaseMusicLottery
```
2. 安装环境依赖 **env python3.6+**
```bash
pip install -r requirement.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

3. 导入数据
mysql中创建数据库 `netease`, 并导入数据结构`netease.sql`

## 使用
1. 写入必要信息
```python
# netease_client.py
#######################
#       账户设置       #
#######################
username = ""
password = ""
user_id = ""
sc_key = ""
# 用户名/密码/用户ID/server酱(用于中奖推送)

#######################
#      程序设置       #
#######################
host = 'localhost'
user = 'root'
pwd = ''
port = 3306
database = 'netease'

# 数据库连接/用户名/密码/端口/库名
```

2. 运行
```bash
python netease_client.py
```

## 流程
1. 扫描分为匹配扫描(页面匹配) 、去重扫描(区间穷举)两种。
2. 中奖检测(1 * 60 * 60 == 3600)，开奖后一小时的动态。
2. 转发时间(12 * 60 * 60 == 43200) ，12小时内开奖的动态。
3. 删除时间(12 * 60 * 60 == 43200) ，开奖后12小时的动态。
5. 中奖标记删除但实际未删除，删除动态每1小时检测但12小时才会删除。
6. 考虑server酱限制，允许错误10次，每次休眠30s，未成功直接跳过。
7. 扫描存储部分8小时一次，会加上去重扫描消耗时间。
8. 错误统一休眠60s一次。
9. 去重扫描实际是阻塞的，部分功能的时间可能会出现延迟。
10. 待添加

ps. 以上的时间并不精准，可能会出现正负值。

## License 许可证
MIT
