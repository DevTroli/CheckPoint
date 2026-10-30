(function () {
  const form = document.getElementById("form-jogo");
  const dialogo = document.getElementById("dialogo");
  const jogoId = form.dataset.jogoId;
  const novo = !jogoId;
  const camposJogo = ["nome", "categoria", "data_lancamento", "desenvolvedora", "publicadora", "descricao"];
  const botaoSalvar = form.querySelector("button[type=submit]");
  const textoSalvar = botaoSalvar.textContent;

  // Só no cadastro: duas etapas (1. o jogo, 2. a avaliação).
  const etapaJogo = document.getElementById("etapa-jogo");
  const etapaAvaliacao = document.getElementById("etapa-avaliacao");
  const marcas = document.querySelectorAll(".etapa-marca");

  let jogoCriadoId = null; // jogo já criado cuja avaliação ainda não foi salva

  function irParaEtapa(numero) {
    etapaJogo.hidden = numero !== 1;
    etapaAvaliacao.hidden = numero !== 2;
    marcas.forEach((marca) => {
      const n = Number(marca.dataset.etapa);
      marca.classList.toggle("ativa", n === numero);
      marca.classList.toggle("feita", n < numero);
    });
    Checkpoint.limparErros(form, dialogo);
    (numero === 1 ? form.elements.nome : form.elements.nota).focus();
  }

  function valoresDoJogo() {
    return Object.fromEntries(camposJogo.map((campo) => [campo, form.elements[campo].value.trim()]));
  }

  function etapaJogoValida() {
    let valida = true;
    [["nome", "Informe o nome do jogo."], ["categoria", "Informe a categoria."], ["data_lancamento", "Informe a data de lançamento."]].forEach(
      ([campo, mensagem]) => {
        if (form.elements[campo].value.trim()) return;
        form.querySelector('[data-erro-para="' + campo + '"]').textContent = mensagem;
        form.elements[campo].setAttribute("aria-invalid", "true");
        valida = false;
      }
    );
    return valida;
  }

  function lerAvaliacao() {
    const nota = Number(form.elements.nota.value);
    if (!Number.isInteger(nota) || nota < 1 || nota > 10) {
      form.querySelector('[data-erro-para="nota"]').textContent = "Informe uma nota inteira de 1 a 10.";
      form.elements.nota.setAttribute("aria-invalid", "true");
      return null;
    }
    const horas = Math.max(0, parseInt(form.elements.horas.value, 10) || 0);
    const minutos = Math.max(0, parseInt(form.elements.minutos.value, 10) || 0);
    return {
      nota: nota,
      tempo_jogado_minutos: horas * 60 + minutos,
      status: form.elements.status.value,
      avaliacao: form.elements.avaliacao.value.trim(),
    };
  }

  function mostrarSucesso(idDoJogo, antes, depois) {
    const partes = ["JOGO ADICIONADO!"];
    const ganho = Checkpoint.textoGanho(antes, depois);
    if (ganho) partes.push(ganho);
    document.getElementById("sucesso-texto").textContent = partes.join(" | ");
    document.getElementById("ver-jogo").href = "/jogos/" + idDoJogo + "/";
    form.hidden = true;
    document.getElementById("etapas").hidden = true;
    document.getElementById("cancelar").hidden = true;
    document.getElementById("form-titulo").textContent = "PRONTO!";
    document.getElementById("sucesso").hidden = false;
  }

  async function salvarEdicao() {
    const resposta = await Checkpoint.api("PUT", "/api/jogos/" + jogoId + "/", valoresDoJogo());
    if (!resposta.ok) return Checkpoint.mostrarErro(form, dialogo, resposta);
    window.location.href = "/jogos/" + resposta.dados.id + "/";
  }

  async function salvarNovo() {
    const avaliacao = lerAvaliacao();
    if (!avaliacao) return;

    if (!jogoCriadoId) {
      const jogo = await Checkpoint.api("POST", "/api/jogos/", valoresDoJogo());
      if (!jogo.ok) {
        irParaEtapa(1);
        return Checkpoint.mostrarErro(form, dialogo, jogo);
      }
      jogoCriadoId = jogo.dados.id;
    }

    const antes = await Checkpoint.gamificacao();
    const registro = await Checkpoint.api("POST", "/api/registros/", Object.assign({ jogo_id: jogoCriadoId }, avaliacao));
    if (!registro.ok) {
      Checkpoint.mostrarErro(form, dialogo, registro);
      if (registro.status !== 400) {
        Checkpoint.mostrarDialogo(dialogo, "O jogo foi criado, mas a avaliação não foi salva. Tente salvar de novo.");
      }
      return;
    }
    const depois = registro.dados.gamificacao;
    if (depois) Checkpoint.atualizarGamificacao(depois);
    mostrarSucesso(jogoCriadoId, antes, depois);
  }

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    Checkpoint.limparErros(form, dialogo);
    botaoSalvar.disabled = true;
    botaoSalvar.textContent = "SALVANDO...";
    try {
      await (novo ? salvarNovo() : salvarEdicao());
    } catch (e) {
      Checkpoint.mostrarDialogo(dialogo, "Sem conexão com o servidor.");
    } finally {
      botaoSalvar.disabled = false;
      botaoSalvar.textContent = textoSalvar;
    }
  });

  if (novo) {
    document.getElementById("proxima").addEventListener("click", () => {
      Checkpoint.limparErros(form, dialogo);
      if (etapaJogoValida()) irParaEtapa(2);
    });
    document.getElementById("voltar").addEventListener("click", () => irParaEtapa(1));
  }

  async function iniciar() {
    const usuario = await Checkpoint.usuario();
    if (!usuario) {
      window.location.href = "/entrar/";
      return;
    }
    if (novo) return;
    const resposta = await Checkpoint.api("GET", "/api/jogos/" + jogoId + "/");
    if (!resposta.ok) {
      Checkpoint.mostrarDialogo(dialogo, resposta.dados.mensagem || "Jogo não encontrado.");
      botaoSalvar.disabled = true;
      return;
    }
    camposJogo.forEach((campo) => (form.elements[campo].value = resposta.dados[campo] || ""));
  }

  iniciar().catch(() => Checkpoint.mostrarDialogo(dialogo, "Sem conexão com o servidor."));
})();
