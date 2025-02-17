# Sistema de Agendamento de Exames Médicos

Este é um sistema web desenvolvido em Python/Flask para gerenciamento de agendamentos de exames médicos. O sistema permite que pacientes agendem exames e que recepcionistas gerenciem estes agendamentos.

## Funcionalidades

- **Pacientes podem:**
  - Agendar exames
  - Visualizar seus agendamentos
  - Cancelar agendamentos
  - Receber notificações por email

- **Recepcionistas podem:**
  - Visualizar todos os agendamentos
  - Agendar exames para pacientes
  - Editar agendamentos
  - Atualizar status dos exames
  - Cancelar agendamentos

## Requisitos

- Python 3.8 ou superior
- MySQL 8.0 ou superior
- Pip (gerenciador de pacotes Python)

## Configuração do Ambiente

1. Clone o repositório:
```bash
git clone [URL_DO_REPOSITORIO]
cd [NOME_DO_DIRETORIO]
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
```

3. Ative o ambiente virtual:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

5. Configure o banco de dados:
- Crie um banco de dados MySQL
- Copie o arquivo `.env.example` para `.env`
- Edite o arquivo `.env` com suas configurações:
```
DB_HOST=localhost
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_NAME=medical_appointments
EMAIL_USER=seu_email@gmail.com
EMAIL_PASSWORD=sua_senha_de_app
```

6. Execute os scripts SQL:
```bash
mysql -u seu_usuario -p medical_appointments < script.sql
```

## Configuração do Email

O sistema usa Gmail para enviar notificações. Para configurar:

1. Ative a verificação em duas etapas na sua conta Google
2. Gere uma senha de aplicativo
3. Use esta senha no arquivo `.env`

## Executando o Sistema

1. Ative o ambiente virtual (se ainda não estiver ativo)

2. Execute o servidor:
```bash
python app.py
```

3. Acesse o sistema:
- Abra o navegador
- Acesse `http://localhost:5000`

## Estrutura do Projeto

- `app.py`: Arquivo principal da aplicação
- `models.py`: Classes e modelos do domínio
- `db.py`: Funções de acesso ao banco de dados
- `routes/`: Rotas da aplicação
  - `auth.py`: Autenticação
  - `paciente.py`: Rotas do paciente
  - `recepcionista.py`: Rotas da recepcionista
- `templates/`: Templates HTML
- `email_service.py`: Serviço de envio de emails
- `tests.py`: Testes unitários

## Executando os Testes

```bash
python -m unittest tests.py -v
```

## Tipos de Exames Disponíveis

- Raio-X
- Ultrassonografia
- Tomografia Computadorizada
- Ressonância Magnética
- Mamografia

## Horários de Funcionamento

- Segunda a Sexta: 08:00 às 18:00
- O sistema não permite agendamentos fora deste horário

## Observações Importantes

1. O sistema verifica a disponibilidade de horários automaticamente
2. Notificações são enviadas por email para:
   - Confirmação de agendamento
   - Cancelamento de exame
   - Alteração de horário
   - Lembretes 24h antes do exame

3. Todos os horários são salvos em UTC
4. É necessário ter um servidor MySQL rodando localmente

## Solução de Problemas

### Problemas Comuns

1. **Erro de conexão com banco de dados**
   - Verifique se o MySQL está rodando
   - Confira as credenciais no arquivo `.env`

2. **Erro no envio de emails**
   - Verifique as configurações do Gmail
   - Confirme se a senha de aplicativo está correta

3. **Erro ao executar os testes**
   - Certifique-se que o banco de dados de teste existe
   - Verifique se todas as dependências estão instaladas

### Logs

Os logs do sistema podem ser encontrados em:
- Logs de aplicação: `app.log`
- Logs de email: `email.log`

## Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature
3. Faça commit das alterações
4. Faça push para a branch
5. Abra um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes. 