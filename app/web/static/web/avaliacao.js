/* Avaliação pessoal do usuário logado para o jogo da página. */
(function () {
  const jogoId = Number(document.getElementById("detalhe").dataset.jogoId);
  const secao = document.getElementById("minha-avaliacao");
  const aviso = document.getElementById("dialogo");
  const pedidoLogin = document.getElementById("avaliacao-login");
  const resumo = document.getElementById("avaliacao-resumo");
  const confirmar = document.getElementById("av-confirmar");
  const form = document.getElementById("form-avaliacao");
  const dialogo = document.getElementById("dialogo-avaliacao");
  const botaoSalvar = form.querySelector("button[type=submit]");
  const botaoCancelar = document.getElementById("av-cancelar");
  const textoSalvar = botaoSalvar.textContent;

  const ganho = document.getElementById("ganho");

  let registro = null;

  /* Mostra o XP (e o streak) conquistados pela ação que acabou de ser salva. */
  function mostrarGanho(antes, depois) {
    const xp = depois.xp - (antes ? antes.xp : 0);
    const streakSubiu = antes && depois.streak > antes.streak;
    if (xp <= 0 && !streakSubiu) {
      ganho.hidden = true;
      return;
    }
    const partes = [];
    if (xp > 0) partes.push("+" + xp + " XP");
    if (streakSubiu) partes.push("STREAK " + depois.streak);
    ganho.textContent = partes.join(" | ");
    ganho.hidden = false;
  }

  function renderizar() {
    confirmar.hidden = true;
    if (registro) {
      document.getElementById("av-nota").textContent = Checkpoint.formatarNota(registro.nota);
      document.getElementById("av-tempo").textContent = Checkpoint.formatarTempo(registro.tempo_jogado_minutos);
      document.getElementById("av-status").textContent = Checkpoint.rotuloStatus(registro.status);
      document.getElementById("av-texto").textContent = registro.avaliacao || "Sem texto de avaliação.";
      resumo.hidden = false;
      form.hidden = true;
    } else {
      resumo.hidden = true;
      abrirFormulario();
    }
  }

  function abrirFormulario() {
    Checkpoint.limparErros(form, dialogo);
    const minutos = registro ? Number(registro.tempo_jogado_minutos) || 0 : 0;
    form.elements.nota.value = registro && Number(registro.nota) > 0 ? Number(registro.nota) : "";
    form.elements.horas.value = Math.floor(minutos / 60);
    form.elements.minutos.value = minutos % 60;
    form.elements.status.value = registro ? registro.status : "concluido";
    form.elements.avaliacao.value = registro ? registro.avaliacao || "" : "";
    botaoCancelar.hidden = !registro;
    form.hidden = false;
  }

  async function iniciar() {
    secao.hidden = false;
    const usuario = await Checkpoint.usuario();
    if (!usuario) {
      pedidoLogin.hidden = false;
      return;
    }
    const resposta = await Checkpoint.api("GET", "/api/registros/");
    if (!resposta.ok) {
      Checkpoint.mostrarDialogo(aviso, "Não foi possível carregar sua avaliação.");
      return;
    }
    registro = resposta.dados.find((item) => Number(item.jogo_id) === jogoId) || null;
    renderizar();
  }

  function lerFormulario() {
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

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    Checkpoint.limparErros(form, dialogo);
    const corpo = lerFormulario();
    if (!corpo) return;

    botaoSalvar.disabled = true;
    botaoSalvar.textContent = "SALVANDO...";
    ganho.hidden = true;
    try {
      const antes = await Checkpoint.gamificacao();
      const resposta = registro
        ? await Checkpoint.api("PATCH", "/api/registros/" + registro.id + "/", corpo)
        : await Checkpoint.api("POST", "/api/registros/", Object.assign({ jogo_id: jogoId }, corpo));
      if (!resposta.ok) return Checkpoint.mostrarErro(form, dialogo, resposta);
      registro = resposta.dados.registro;
      renderizar();
      const depois = resposta.dados.gamificacao;
      if (depois) {
        Checkpoint.atualizarGamificacao(depois);
        mostrarGanho(antes, depois);
      }
    } catch (e) {
      Checkpoint.mostrarDialogo(dialogo, "Sem conexão com o servidor.");
    } finally {
      botaoSalvar.disabled = false;
      botaoSalvar.textContent = textoSalvar;
    }
  });

  document.getElementById("av-editar").addEventListener("click", () => {
    resumo.hidden = true;
    abrirFormulario();
  });
  botaoCancelar.addEventListener("click", renderizar);

  document.getElementById("av-excluir").addEventListener("click", () => {
    confirmar.hidden = false;
  });
  document.getElementById("av-confirmar-nao").addEventListener("click", () => {
    confirmar.hidden = true;
  });
  document.getElementById("av-confirmar-sim").addEventListener("click", async () => {
    try {
      const resposta = await Checkpoint.api("DELETE", "/api/registros/" + registro.id + "/");
      if (!resposta.ok) {
        confirmar.hidden = true;
        Checkpoint.mostrarDialogo(aviso, resposta.dados.mensagem || "Não foi possível excluir.");
        return;
      }
      registro = null;
      renderizar();
    } catch (e) {
      Checkpoint.mostrarDialogo(aviso, "Sem conexão com o servidor.");
    }
  });

  // Só aparece depois que o jogo foi carregado (jogo inexistente não é avaliável).
  document.addEventListener("jogo-carregado", () => {
    iniciar().catch(() => Checkpoint.mostrarDialogo(aviso, "Sem conexão com o servidor."));
  });
})();
