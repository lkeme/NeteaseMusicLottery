# NeteaseMusicLottery

## 公告
网易云音乐动态互动抽奖测试学习

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

3. 导入数据文件
mysql中创建数据库 `netease`， 并导入数据结构`netease.sql`
```sql
create DATABASE netease;
use netease;
source /your path/netease.sql;
```

4. 复制配置文件
```bash
# linux
cd Config && cp setting.py.example setting.py
# windows
手动重命名 
```

5. 填写配置信息
```python
# 修改文件 --> Config/setting.py 
# """ 网易云账号配置 """
ACCOUNTS = [
    # default 扫描账号 (扫描、转发、删除等) 必须定义一个
    # valid 有效账号 (转发、删除等) 视情况定义增加
    # invalid 无效账号 (不做任何操作)
    {
        "user_id": "",
        "username": "",
        "password": "",
        "type": "default",
    },
    {
        "user_id": "0",
        "username": "your user name",
        "password": "your password",
        "type": "invalid",
    },
    {
        "user_id": "0",
        "username": "your user name",
        "password": "your password",
        "type": "invalid",
    }
]

""" 通知服务配置 """
NOTIFICATION = {
    # 开关
    "enable": True,
    "type": "server_chan",
    # Server酱
    "server_chan":
        {
            "key": "",
        },
    # tg_bot  https://github.com/Fndroid/tg_push_bot
    "tg_bot":
        {
            "api": "https://xxxx.com/sendMessage/:Token",
        },
    # 自用通知服务
    "personal":
        {
            "url": "",
            "channel": ""
        }
}

""" MYSQL数据库配置 """
DATABASES = {
    "default": {
        "HOST": "localhost",
        "PORT": 3306,
        "USERNAME": "root",
        "PASSWORD": "123456",
        "DATABASE": "netease",
    }
}
```

## 使用
```bash
python main.py
```

## 打赏

![](https://i.loli.net/2019/07/13/5d2963e5cc1eb22973.png)

## 流程
1. 扫描分为匹配扫描(页面匹配) 、去重扫描(区间穷举)两种。
2. 中奖检测(1 * 60 * 60 == 3600)，开奖后一小时的动态。
2. 转发时间(12 * 60 * 60 == 43200) ，12小时内开奖的动态。
3. 删除时间(6 * 60 * 60 == 21600) ，开奖后6小时的动态。
5. 中奖标记删除但实际未删除，删除动态每1小时检测但12小时才会删除。
6. 考虑server酱限制，允许错误10次，每次休眠30s，未成功直接跳过。
7. 完整扫描部分4小时一次， 防止异常，分段扫描， 每段1000(可调节)。
7. 迷你扫描部分14小时一次， 会加上去重扫描消耗时间，理论时间不和完整扫描冲突。
8. 错误统一休眠60s一次。
9. 去重扫描实际是阻塞的，部分功能的时间可能会出现延迟。
10. 自用设置不用管，留空就行

ps. 以上的时间并不精准，可能会出现正负值。

## License 许可证
MIT
