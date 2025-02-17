import unittest
from datetime import datetime, timedelta
from models import Paciente, Recepcionista, Agendamento, Notificacao, Exame
from db import (
    verificar_disponibilidade, agendar_exame, 
    cancelar_agendamento, get_paciente_by_user_id,
    editar_agendamento, get_agendamento, get_notificacoes_paciente
)

class TestAgendamentoExames(unittest.TestCase):
    def setUp(self):
        print("\nConfigurando teste...")
        # Criar paciente de teste
        self.paciente = Paciente(
            id=1,
            username="teste",
            nome="Paciente Teste",
            email="teste@example.com",
            cpf="12345678900",
            data_nascimento=datetime(1990, 1, 1),
            user_id=1
        )
        
        # Criar recepcionista de teste
        self.recepcionista = Recepcionista(
            id=1,
            username="recep",
            nome="Recepcionista Teste",
            email="recep@example.com",
            user_id=2
        )
        
        # Data/hora para testes
        self.data_hora = datetime.now() + timedelta(days=1)
        self.data_hora = self.data_hora.replace(hour=10, minute=0, second=0, microsecond=0)
        print("Configuração concluída.")

    def test_verificar_disponibilidade(self):
        """US1: Verificar se o horário está disponível"""
        print("\nTestando verificação de disponibilidade...")
        disponivel = verificar_disponibilidade(self.data_hora)
        self.assertTrue(disponivel, "O horário deveria estar disponível")
        print("Teste de disponibilidade concluído.")

    def test_agendar_exame_paciente(self):
        """US1: Agendamento de exame pelo paciente"""
        print("\nTestando agendamento de exame pelo paciente...")
        # Criar agendamento
        agendamento = self.paciente.agendar_exame("Raio-X", self.data_hora)
        
        # Verificar se o agendamento foi criado corretamente
        self.assertIsNotNone(agendamento)
        self.assertEqual(agendamento.paciente, self.paciente)
        self.assertEqual(agendamento.exame.tipo_exame, "Raio-X")
        self.assertEqual(agendamento.data_hora, self.data_hora)
        self.assertEqual(agendamento.status, "agendado")
        print("Teste de agendamento pelo paciente concluído.")

    def test_notificacao_agendamento(self):
        """US3: Teste de notificação de agendamento"""
        print("\nTestando notificação de agendamento...")
        # Criar agendamento
        agendamento = Agendamento(
            paciente=self.paciente,
            tipo_exame="Raio-X",
            data_hora=self.data_hora
        )
        
        # Criar e anexar notificação
        notificacao = Notificacao()
        agendamento.attach(notificacao)
        
        # Notificar
        agendamento.notify()
        
        # Verificar se a mensagem foi criada
        self.assertTrue(len(notificacao.mensagens) > 0)
        ultima_mensagem = notificacao.mensagens[-1]
        
        # Verificar conteúdo da mensagem
        self.assertEqual(ultima_mensagem['paciente_id'], self.paciente.id)
        self.assertEqual(ultima_mensagem['email_destino'], self.paciente.email)
        self.assertIn(self.paciente.nome, ultima_mensagem['mensagem'])
        self.assertIn("Raio-X", ultima_mensagem['mensagem'])
        self.assertIn(self.data_hora.strftime("%d/%m/%Y às %H:%M"), ultima_mensagem['mensagem'])
        print("Teste de notificação concluído.")

    def test_cancelamento_agendamento(self):
        """US2: Teste de cancelamento de agendamento"""
        print("\nTestando cancelamento de agendamento...")
        # Criar agendamento
        agendamento = Agendamento(
            id=1,
            paciente=self.paciente,
            tipo_exame="Raio-X",
            data_hora=self.data_hora
        )
        
        # Criar e anexar notificação
        notificacao = Notificacao()
        agendamento.attach(notificacao)
        
        # Cancelar agendamento
        resultado = agendamento.cancelar()
        
        # Verificar se o cancelamento foi bem-sucedido
        self.assertTrue(resultado)
        self.assertEqual(agendamento.status, "cancelado")
        self.assertEqual(agendamento.exame.status, "cancelado")
        
        # Verificar se a notificação de cancelamento foi criada
        ultima_mensagem = notificacao.mensagens[-1]
        self.assertIn("cancelado", ultima_mensagem['mensagem'])
        print("Teste de cancelamento concluído.")

    def test_agendamento_recepcionista(self):
        """US2: Teste de agendamento pela recepcionista"""
        print("\nTestando agendamento pela recepcionista...")
        # Recepcionista agenda exame para paciente
        agendamento = self.recepcionista.agendar_exame(
            paciente=self.paciente,
            tipo_exame="Ultrassonografia",
            data_hora=self.data_hora
        )
        
        # Verificar se o agendamento foi criado corretamente
        self.assertIsNotNone(agendamento)
        self.assertEqual(agendamento.paciente, self.paciente)
        self.assertEqual(agendamento.exame.tipo_exame, "Ultrassonografia")
        self.assertEqual(agendamento.status, "agendado")
        print("Teste de agendamento pela recepcionista concluído.")

    def test_edicao_agendamento_recepcionista(self):
        """US4: Teste de edição de agendamento pela recepcionista"""
        print("\nTestando edição de agendamento pela recepcionista...")
        
        # Criar agendamento inicial
        print("Criando agendamento inicial...")
        agendamento = self.recepcionista.agendar_exame(
            paciente=self.paciente,
            tipo_exame="Raio-X",
            data_hora=self.data_hora
        )
        
        # Nova data e tipo de exame para edição
        nova_data = self.data_hora + timedelta(days=1)
        novo_tipo = "Ultrassonografia"
        
        print(f"Tentando editar agendamento {agendamento.id}...")
        print(f"Novo tipo: {novo_tipo}")
        print(f"Nova data: {nova_data}")
        
        # Editar agendamento
        resultado = editar_agendamento(agendamento.id, novo_tipo, nova_data)
        
        # Verificar se a edição foi bem-sucedida
        self.assertTrue(resultado, "A edição do agendamento falhou")
        
        # Buscar agendamento atualizado
        print("Buscando agendamento atualizado...")
        agendamento_atualizado = get_agendamento(agendamento.id)
        self.assertIsNotNone(agendamento_atualizado, "Agendamento não encontrado após edição")
        
        print("Verificando dados atualizados...")
        self.assertEqual(agendamento_atualizado.tipo_exame, novo_tipo, 
                        f"Tipo de exame não foi atualizado. Esperado: {novo_tipo}, Atual: {agendamento_atualizado.tipo_exame}")
        self.assertEqual(agendamento_atualizado.data_hora, nova_data,
                        f"Data/hora não foi atualizada. Esperado: {nova_data}, Atual: {agendamento_atualizado.data_hora}")
        
        # Verificar notificações
        print("Verificando notificações...")
        notificacoes = get_notificacoes_paciente(self.paciente.id)
        self.assertTrue(len(notificacoes) > 0, "Nenhuma notificação encontrada")
        
        ultima_notificacao = notificacoes[-1]
        self.assertIn("remarcado", ultima_notificacao.mensagem, "Mensagem de remarcação não encontrada")
        self.assertIn(novo_tipo, ultima_notificacao.mensagem, "Novo tipo de exame não encontrado na mensagem")
        self.assertIn(nova_data.strftime("%d/%m/%Y às %H:%M"), ultima_notificacao.mensagem,
                     "Nova data não encontrada na mensagem")
        
        print("Teste de edição concluído.")

if __name__ == '__main__':
    unittest.main() 