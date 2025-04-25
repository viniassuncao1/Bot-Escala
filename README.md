# 🚨 Bot de Escala – Recepção Discord

Sistema completo para gerenciamento de escala de presença (recepção) em servidores RP via Discord.
Com integração ao Google Sheets, painel interativo, controle automático de responsáveis e geração de logs profissionais.

## ✨ Principais Recursos
- ✅ Entradas e saídas automáticas com registro em tempo real
- 📊 Integração com Google Sheets para relatórios e auditoria
- 📋 Painel fixo informativo sempre visível no canal
- 👮 Controle de responsáveis (SD+) e limite de policiais simultâneos
- 📢 Logs automáticos em canal próprio
- ⚙️ Comandos de administração para resetar ou revisar escalas

## 🚀 Como Rodar Localmente
1. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
2. Crie o arquivo `.env` com as variáveis de ambiente:

   | Variável              | Descrição                                              |
   |----------------------|--------------------------------------------------------|
   | TOKEN_DISCORD        | Token do seu bot no Discord                            |
   | GUILD_ID             | ID do servidor                                         |
   | LOG_CHANNEL_ID       | ID do canal onde os logs serão enviados                |
   | ESCALA_CHANNEL_ID    | ID do canal onde a escala ficará ativa                 |
   | LOGO_URL             | URL da imagem/logo a ser usada nas embeds              |
   | SHEETS_JSON          | Nome do arquivo JSON das credenciais                   |
   | SHEETS_NOME          | Nome da planilha do Google Sheets                      |
   | ALTO_COMANDO_ROLE_ID | ID do cargo autorizado para comandos avançados         |

3. Coloque o JSON de credenciais do Google na pasta raiz do projeto.
4. Rode o projeto:
   ```bash
   python app.py
   ```

## ⚠️ Observações Importantes
- 🔒 Nunca suba os arquivos `.env` ou `.json` com credenciais no repositório.
- 🔧 O comando `/resetar_escala` só pode ser utilizado por usuários com cargo autorizado.
- 🧾 Todos os registros são salvos automaticamente no Google Sheets.

## 📞 Suporte
Em caso de dúvidas ou sugestões, procure o responsável pelo bot no Discord ou abra uma issue neste repositório.
