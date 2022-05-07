# 校园网认证客户端

如题。

## Usage

可以直接运行
```sh
python3 networkd.py
```

也可以调用 `campus.py` 实现自己的逻辑。

```python
from campus import CampusNetwork
daemon = CampusNetwork()

# 可以手动指定认证 IP
daemon = CampusNetwork('1.2.3.4')
```

## Methods

1. 监听网络状态改变

   ```python
   daemon.listen_for_network_change([interval], [callback])
   ```

   |参数|类型|说明|
   |-|-|-|
   |`interval`|`int`|检查的时间间隔，单位：秒|
   |`callback`|`Function[str] -> None`|回调函数，参数为状态|

2. 登陆和登出

   ```python
   daemon.login([username], [password], [service])
   daemon.logout()
   ```

   |参数|类型|说明|
   |-|-|-|
   |`username`|`str`|用户名|
   |`password`|`str`|密码|
   |`service`|`str`|服务类型|

3. 获取服务

   ```python
   daemon.service_names
   ```

   |类型|说明|
   |-|-|
   |`List[str]`|服务名|
