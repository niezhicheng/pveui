apt install -y \
    curl \
    gnupg \
    apt-transport-https \
    ca-certificates \
    software-properties-common -y


 # 创建目录
mkdir -p /etc/apt/keyrings

# 添加阿里云 Docker GPG 密钥
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 添加阿里云 Docker 仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# 更新包列表
apt update

apt install -y docker-ce docker-ce-cli containerd.io

# 启动 Docker 服务
systemctl enable docker
systemctl start docker

新建一个docker-compose.yaml 然后把项目代码这的docker-compose.yaml 的内容粘贴过去
或者直接scp docker-compose.yaml 到pve 然后
docker-compose up -d
启动访问pve 的8012 端口即可
默认账号admin 密码admin123