# 云端部署手册（Ubuntu 22.04）

这套部署默认：
- `systemd` 管理 `uvicorn`
- `nginx` 反向代理到 `127.0.0.1:8000`
- 可选 `certbot` 自动签发 HTTPS

## 1. 安装系统依赖

```bash
cd /opt/finance-agent
bash deploy/scripts/install_deps_ubuntu.sh
```

## 2. 拉代码并安装项目

```bash
sudo mkdir -p /opt/finance-agent
sudo chown -R $USER:$USER /opt/finance-agent
cd /opt/finance-agent
# 这里换成你的仓库地址
git clone <YOUR_GIT_REPO_URL> .

bash deploy/scripts/setup_app.sh /opt/finance-agent
```

## 3. 配置环境变量

```bash
cd /opt/finance-agent
nano .env
```

至少配置：
- `TUSHARE_TOKEN`
- `OLLAMA_HOST`（如果 Ollama 不在本机，需要写远程地址）
- `AUTH_TOKEN_TTL_HOURS`

## 4. 生成部署配置

```bash
cd /opt/finance-agent
# 参数: APP_DIR DOMAIN RUN_USER RUN_GROUP
bash deploy/scripts/render_configs.sh /opt/finance-agent your-domain.com $USER $USER
```

如果先用 IP 访问，`DOMAIN` 可填 `_`：

```bash
bash deploy/scripts/render_configs.sh /opt/finance-agent _ $USER $USER
```

## 5. 安装 systemd 和 nginx

```bash
cd /opt/finance-agent
sudo cp deploy/generated/finance-agent.service /etc/systemd/system/finance-agent.service
sudo cp deploy/generated/finance-agent.nginx.conf /etc/nginx/sites-available/finance-agent
sudo ln -sf /etc/nginx/sites-available/finance-agent /etc/nginx/sites-enabled/finance-agent
sudo rm -f /etc/nginx/sites-enabled/default

sudo systemctl daemon-reload
sudo systemctl enable --now finance-agent
sudo nginx -t
sudo systemctl restart nginx
```

## 6. 验证

```bash
systemctl status finance-agent --no-pager
curl http://127.0.0.1:8000/health
curl http://<你的服务器IP>/health
```

## 7. 启用 HTTPS（可选）

域名已解析到服务器后执行：

```bash
sudo certbot --nginx -d your-domain.com
```

证书续期检查：

```bash
sudo certbot renew --dry-run
```

## 8. 常用运维命令

```bash
sudo systemctl restart finance-agent
sudo systemctl stop finance-agent
sudo systemctl start finance-agent
sudo journalctl -u finance-agent -n 100 --no-pager
```

## 9. 更新发布流程

```bash
cd /opt/finance-agent
git pull
.venv/bin/pip install -r requirements.txt
sudo systemctl restart finance-agent
```
