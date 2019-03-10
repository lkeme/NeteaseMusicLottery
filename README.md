# NeteaseMusicLottery
网易云音乐动态互动抽奖  / Netease Cloud Music Dynamics Lottery Draw

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

## License 许可证
MIT
