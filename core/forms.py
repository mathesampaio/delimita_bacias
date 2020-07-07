from django import forms
from django.core.mail.message import EmailMessage



class ContatoForms(forms.Form):
    nome = forms.CharField(label = 'Nome', max_length=100)
    email = forms.EmailField(label = 'E-mail', max_length=100)
    assunto = forms.CharField(label = 'Assunto', max_length=100)
    mensagem = forms.CharField(label = 'Mensagem', widget=forms.Textarea())

    def send_mail(self):
        nome = self.cleaned_data['nome']
        email = self.cleaned_data['email']
        assunto = self.cleaned_data['assunto']
        mensagem = self.cleaned_data['mensagem']

        conteudo = f'Nome: {nome}\n Email: {email}\n Assunto: {assunto}\nMensagem: {mensagem}\n'

        mail = EmailMessage(
            subject=assunto,
            body=conteudo,
            from_email='ejhidrica@gmail.com',
            to=['ejhidrica@gmail.com',],
            headers={'Reply-To': email}
        )
        mail.send()
