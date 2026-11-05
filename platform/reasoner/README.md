# reasoner

`reasoner` 是 ROBOT/ELK 推理与 SHACL 校验的薄 HTTP 包装（`app.py`，端口 7879）。

## robot.jar 说明

`Dockerfile` 中有一行：

```dockerfile
COPY robot.jar /opt/robot/robot.jar
```

`robot.jar` 约 93 MB，超过仓库单文件限制，**未纳入版本库**（见 `platform/.gitignore`）。
在构建镜像前必须手动放置：

```powershell
# 任选其一
# 1) 从内部工作副本复制
Copy-Item D:\agentABC\_impl\reasoner\robot.jar D:\path\to\repo\platform\reasoner\robot.jar
# 2) 从官方发布页下载（版本需与 ROBOT 5.x 对齐）
#    https://github.com/ontodev/robot/releases
```

未放置 `robot.jar` 时 `docker compose build reasoner` 会在 COPY 处失败，平台其余服务不受影响
（`platform` 不以 `reasoner` 为依赖，缺失时推理接口返回 `E_REASONER_UNAVAILABLE`）。
