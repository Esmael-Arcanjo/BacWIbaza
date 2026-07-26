



# 1. Criar o ambiente virtual
python -m venv venv

# 2. Ativar o ambiente virtual
source venv/bin/activate


# 3. Atualizar o pip e instalar as dependências
pip install --upgrade pip
pip install -r requirements.txt




# 1. Adicionar o repositório deadsnakes (necessário no Ubuntu 22.04 para ter o Python 3.11 completo)
sudo add-apt-repository ppa:deadsnakes/ppa -y

# 2. Atualizar os pacotes
sudo apt update

# 3. Instalar o Python 3.11 e o pacote de ambiente virtual
sudo apt install -y python3.11 python3.11-venv python3.11-dev



# Entrar na pasta do projeto
cd ~/Documentos/SaaSLeamse/SaaSbackend

# Remover a venv antiga (Python 3.10)
rm -rf venv

# Criar a nova venv apontando especificamente para o Python 3.11
python3.11 -m venv venv

# Ativar a venv
source venv/bin/activate

# Atualizar os gerenciadores do pip
pip install --upgrade pip setuptools wheel

# Instalar suas dependências
pip install -r requirements.txt


rodar

source venv/bin/activate

uvicorn server:app --reload


git add .
git commit -m "atualizando"
git push origin main

