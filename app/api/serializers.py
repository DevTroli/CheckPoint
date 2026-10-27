from rest_framework import serializers


class CadastroUsuarioSerializer(serializers.Serializer):
    nome_usuario = serializers.CharField(min_length=3, max_length=50)
    email = serializers.EmailField()
    senha = serializers.CharField(min_length=6, max_length=128, write_only=True)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    senha = serializers.CharField(write_only=True)


class AtualizacaoUsuarioSerializer(serializers.Serializer):
    nome_usuario = serializers.CharField(min_length=3, max_length=50, required=False)
    email = serializers.EmailField(required=False)
    senha = serializers.CharField(min_length=6, max_length=128, required=False, write_only=True)


class JogoSerializer(serializers.Serializer):
    nome = serializers.CharField(min_length=1, max_length=150)
    descricao = serializers.CharField(required=False, allow_blank=True)
    categoria = serializers.CharField(min_length=1, max_length=80)
    data_lancamento = serializers.DateField(input_formats=["%Y-%m-%d"])
    publicadora = serializers.CharField(required=False, allow_blank=True, max_length=120)
    desenvolvedora = serializers.CharField(required=False, allow_blank=True, max_length=120)


class RegistroSerializer(serializers.Serializer):
    jogo_id = serializers.IntegerField(min_value=1)
    progresso = serializers.IntegerField(min_value=0, max_value=100, required=False, default=0)
    tempo_jogado_minutos = serializers.IntegerField(min_value=0, required=False, default=0)
    nota = serializers.FloatField(min_value=0, max_value=10, required=False, default=0)
    status = serializers.ChoiceField(
        choices=["planejado", "jogando", "pausado", "abandonado", "concluido"],
        required=False,
        default="planejado",
    )
    avaliacao = serializers.CharField(required=False, allow_blank=True, max_length=2000)


class AtualizacaoRegistroSerializer(serializers.Serializer):
    progresso = serializers.IntegerField(min_value=0, max_value=100, required=False)
    tempo_jogado_minutos = serializers.IntegerField(min_value=0, required=False)
    nota = serializers.FloatField(min_value=0, max_value=10, required=False)
    status = serializers.ChoiceField(
        choices=["planejado", "jogando", "pausado", "abandonado", "concluido"],
        required=False,
    )
    avaliacao = serializers.CharField(required=False, allow_blank=True, max_length=2000)
