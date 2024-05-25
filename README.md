# Conversor de Arquivos Chart/SNG

Este projeto permite converter arquivos .chart para .sng e vice-versa. Você pode baixar o executável diretamente e utilizá-lo sem precisar instalar o Python.

## Como Usar

1. Baixe o arquivo `conversor.exe` da seção de releases.
2. Execute o arquivo baixado.
3. Use a interface gráfica para selecionar e converter seus arquivos.

## Requisitos

- Windows 7 ou superior

## Compilação

Se você quiser compilar o executável você mesmo, siga os passos abaixo:

1. Clone o repositório.
2. Instale as dependências com `pip install pyinstaller`.
3. Compile o executável com `pyinstaller --onefile --windowed --icon=icon.ico conversor.py`.
4. O executável será criado na pasta `dist`.
