import unittest
from datetime import datetime, timedelta
from models import Paciente, Recepcionista, Agendamento, Notificacao, Exame
from db import (
    verificar_disponibilidade, agendar_exame, 
    cancelar_agendamento, get_paciente_by_user_id
)

class TestAgendamentoExames(unittest.TestCase):
    def setUp(self):
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

    def test_verificar_disponibilidade(self):
        """US1: Verificar se o horário está disponível"""
        disponivel = verificar_disponibilidade(self.data_hora)
        self.assertTrue(disponivel, "O horário deveria estar disponível")

    def test_agendar_exame_paciente(self):
        """US1: Agendamento de exame pelo paciente"""
        # Criar agendamento
        agendamento = self.paciente.agendar_exame("Raio-X", self.data_hora)
        
        # Verificar se o agendamento foi criado corretamente
        self.assertIsNotNone(agendamento)
        self.assertEqual(agendamento.paciente, self.paciente)
        self.assertEqual(agendamento.exame.tipo_exame, "Raio-X")
        self.assertEqual(agendamento.data_hora, self.data_hora)
        self.assertEqual(agendamento.status, "agendado")

    def test_notificacao_agendamento(self):
        """US3: Teste de notificação de agendamento"""
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

    def test_cancelamento_agendamento(self):
        """US2: Teste de cancelamento de agendamento"""
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

    def test_agendamento_recepcionista(self):
        """US2: Teste de agendamento pela recepcionista"""
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

if __name__ == '__main__':
    unittest.main() 