# reasoner

`reasoner` 是 ROBOT/ELK 推理与 SHACL 校验的薄 HTTP 包装（`app.py`，端口 7879）。

## robot.jar 说明

`Dockerfile` 不再 `COPY robot.jar`，改为**构建时自动下载**官方的 ROBOT 1.9.6 release
（`https://github.com/ontodev/robot/releases/download/v1.9.6/robot.jar`，93,636,279 字节）
到镜像内 `/opt/robot/robot.jar`，并用 `sha256sum -c` 校验
（`3d112f47a5c2e82fd96c2bc40e582a86d1e6ad24f67648ef103ec5f21985ba5e`）。
`curl -f` 返回非 0（HTTP ≥ 400）或下载后文件为空都会**直接让构建失败**，不会留下空 jar。

`robot.jar` 约 93 MB，超过仓库单文件限制，**仍不纳入版本库**（见 `packages/platform-core/.gitignore`）。

```powershell
# 标准（联网）
docker compose -f packages/platform-core/docker-compose.yml build reasoner

# 换源/关校验
docker compose -f packages/platform-core/docker-compose.yml build reasoner `
  --build-arg ROBOT_JAR_URL=https://github.com/ontodev/robot/releases/download/v1.9.6/robot.jar `
  --build-arg ROBOT_JAR_SHA256=3d112f47a5c2e82fd96c2bc40e582a86d1e6ad24f67648ef103ec5f21985ba5e
```

离线/内网替代路径（内网制品库改 URL；完全隔离则 `ROBOT_JAR_URL=` + 运行时挂载 jar）
见 `../RUN.md` 第 2 节。

校验：

```powershell
docker run --rm agent-reasoner:0.1-s5 java -jar /opt/robot/robot.jar --version
# ROBOT version 1.9.6
```

实测（2026-11-05，Docker Desktop 29.9.2）：构建 **104.3 s**，镜像 **383 MB**，其中 jar 层 **93.6 MB**；
容器内 `java -jar /opt/robot/robot.jar --version` 输出 `ROBOT version 1.9.6`。
本机 GitHub 直链约 32 KB/s，构建验证时用代理源
`https://gh-proxy.com/https://github.com/ontodev/robot/releases/download/v1.9.6/robot.jar`
（`sha256sum -c` 通过，字节与官方一致）；把 URL 指向 404 时构建退出码 1。

未放置/未下载到 `robot.jar` 时镜像仍可构建（仅在显式传 `ROBOT_JAR_URL=` 时），
但运行时缺 jar 会让推理接口返回 `E_REASONER_UNAVAILABLE`，平台其余服务不受影响。
