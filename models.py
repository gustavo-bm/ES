from abc import ABC, abstractmethod
from datetime import datetime
from typing import List
from email_utils import enviar_email

class Observer(ABC):
    @abstractmethod
    def update(self, agendamento: 'Agendamento') -> None:
        pass

class Subject(ABC):
    @abstractmethod
    def attach(self, observer: Observer) -> None:
        pass

    @abstractmethod
    def detach(self, observer: Observer) -> None:
        pass

    @abstractmethod
    def notify(self) -> None:
        pass

class Usuario:
    def __init__(self, id: int, username: str, nome: str, email: str, tipo_usuario: str):
        self.id = id
        self.username = username
        self.nome = nome
        self.email = email
        self.tipo_usuario = tipo_usuario

class Paciente(Usuario):
    def __init__(self, id: int, username: str, nome: str, email: str, 
                 cpf: str, data_nascimento: datetime, user_id: int):
        super().__init__(id, username, nome, email, 'paciente')
        self.cpf = cpf
        self.data_nascimento = data_nascimento
        self.user_id = user_id
        self.agendamentos: List[Agendamento] = []

    def agendar_exame(self, tipo_exame: str, data_hora: datetime) -> 'Agendamento':
        agendamento = Agendamento(self, tipo_exame, data_hora)
        self.agendamentos.append(agendamento)
        return agendamento

class Recepcionista(Usuario):
    def __init__(self, id: int, username: str, nome: str, email: str, user_id: int):
        super().__init__(id, username, nome, email, 'recepcionista')
        self.user_id = user_id

    def agendar_exame(self, paciente: Paciente, tipo_exame: str, data_hora: datetime) -> 'Agendamento':
        return paciente.agendar_exame(tipo_exame, data_hora)

    def atualizar_status_exame(self, exame: 'Exame', novo_status: str) -> bool:
        return exame.atualizar_status(novo_status)

class Exame:
    def __init__(self, id: int, tipo_exame: str, data_hora: datetime, status: str = 'agendado'):
        self.id = id
        self.tipo_exame = tipo_exame
        self.data_hora = data_hora
        self.status = status

    def atualizar_status(self, novo_status: str) -> bool:
        self.status = novo_status
        return True

class Agendamento(Subject):
    def __init__(self, paciente: Paciente, tipo_exame: str, data_hora: datetime, 
                 status: str = 'agendado', id: int = None):
        self.id = id
        self.paciente = paciente
        self.exame = Exame(id=None, tipo_exame=tipo_exame, data_hora=data_hora)
        self.data_hora = data_hora
        self.status = status
        self._observers: List[Observer] = []

    def attach(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)

    def notify(self) -> None:
        for observer in self._observers:
            observer.update(self)

    def cancelar(self) -> bool:
        self.status = 'cancelado'
        self.exame.status = 'cancelado'
        self.notify()
        return True

class Notificacao(Observer):
    def __init__(self, id: int = None):
        self.id = id
        self.mensagens: List[dict] = []

    def update(self, agendamento: Agendamento) -> None:
        mensagem = self._criar_mensagem(agendamento)
        self.mensagens.append({
            'paciente_id': agendamento.paciente.id,
            'mensagem': mensagem,
            'email_destino': agendamento.paciente.email,
            'status_envio': 'pendente'
        })
        self._enviar_email(agendamento.paciente.email, mensagem)

    def _criar_mensagem(self, agendamento: Agendamento) -> str:
        if agendamento.status == 'cancelado':
            return f'''Olá {agendamento.paciente.nome},

Seu exame de {agendamento.exame.tipo_exame} agendado para {agendamento.data_hora.strftime("%d/%m/%Y às %H:%M")} foi cancelado.'''
        else:
            return f'''Olá {agendamento.paciente.nome},

Seu exame de {agendamento.exame.tipo_exame} foi agendado com sucesso para {agendamento.data_hora.strftime("%d/%m/%Y às %H:%M")}.

Por favor, chegue com 15 minutos de antecedência.'''

    def _enviar_email(self, email_destino: str, mensagem: str) -> bool:
        assunto = 'Cancelamento de Exame' if 'cancelado' in mensagem else 'Confirmação de Agendamento'
        return enviar_email(email_destino, assunto, mensagem) 