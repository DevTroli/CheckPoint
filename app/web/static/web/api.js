/* Utilitários compartilhados pelas páginas. Todo texto vindo da API entra na
   página via textContent (nunca innerHTML), para que dados não virem HTML. */
(function () {
  const Checkpoint = (window.Checkpoint = window.Checkpoint || {});

  /* Separador dos avisos em fonte pixel; o "|" dessa fonte parece um "I" colado no texto. */
  Checkpoint.separador = " - ";

  Checkpoint.api = async function (metodo, url, corpo) {
    const opcoes = { method: metodo, credentials: "same-origin", headers: {} };
    if (corpo !== undefined) {
      opcoes.headers["Content-Type"] = "application/json";
      opcoes.body = JSON.stringify(corpo);
    }
    const resposta = await fetch(url, opcoes);
    let dados = null;
    try {
      dados = await resposta.json();
    } catch (e) {
      /* resposta sem corpo JSON (ex.: 204) */
    }
    return { ok: resposta.ok, status: resposta.status, dados: dados || {} };
  };

  let usuarioPromessa = null;
  Checkpoint.usuario = function () {
    if (!usuarioPromessa) {
      usuarioPromessa = Checkpoint.api("GET", "/api/usuarios/me/")
        .then((r) => (r.ok ? r.dados : null))
        .catch(() => null);
    }
    return usuarioPromessa;
  };

  /* XP, streak e posição do usuário logado; compartilhado entre cabeçalho e páginas. */
  let gamificacaoPromessa = null;
  Checkpoint.gamificacao = function () {
    if (!gamificacaoPromessa) {
      gamificacaoPromessa = Checkpoint.api("GET", "/api/gamificacao/me/")
        .then((r) => (r.ok ? r.dados : null))
        .catch(() => null);
    }
    return gamificacaoPromessa;
  };

  Checkpoint.atualizarGamificacao = function (dados) {
    gamificacaoPromessa = Promise.resolve(dados);
    document.dispatchEvent(new CustomEvent("gamificacao-atualizada", { detail: dados }));
  };

  /* "+25 XP - STREAK 3" com o que mudou entre antes e depois; vazio se nada mudou. */
  Checkpoint.textoGanho = function (antes, depois) {
    if (!depois) return "";
    const partes = [];
    const xp = depois.xp - (antes ? antes.xp : 0);
    if (xp > 0) partes.push("+" + xp + " XP");
    if (antes && depois.streak > antes.streak) partes.push("STREAK " + depois.streak);
    return partes.join(Checkpoint.separador);
  };

  Checkpoint.el = function (tag, atributos, ...filhos) {
    const no = document.createElement(tag);
    Object.entries(atributos || {}).forEach(([nome, valor]) => no.setAttribute(nome, valor));
    filhos.forEach((filho) => no.append(filho));
    return no;
  };

  Checkpoint.limparErros = function (form, dialogo) {
    dialogo.hidden = true;
    dialogo.textContent = "";
    form.querySelectorAll("[data-erro-para]").forEach((el) => (el.textContent = ""));
    form.querySelectorAll("[aria-invalid]").forEach((el) => el.removeAttribute("aria-invalid"));
  };

  Checkpoint.mostrarDialogo = function (dialogo, mensagem) {
    dialogo.textContent = mensagem;
    dialogo.hidden = false;
  };

  /* 400 -> mensagens sob cada campo; demais -> caixa de diálogo. */
  Checkpoint.mostrarErro = function (form, dialogo, resposta) {
    const { status, dados } = resposta;
    if (status === 400) {
      let algumCampo = false;
      Object.entries(dados).forEach(([campo, mensagens]) => {
        const alvo = form.querySelector('[data-erro-para="' + campo + '"]');
        if (!alvo) return;
        algumCampo = true;
        alvo.textContent = [].concat(mensagens).join(" ");
        const entrada = form.elements[campo];
        if (entrada) entrada.setAttribute("aria-invalid", "true");
      });
      if (!algumCampo) Checkpoint.mostrarDialogo(dialogo, "Confira os dados informados.");
      return;
    }
    Checkpoint.mostrarDialogo(dialogo, dados.mensagem || "Algo deu errado. Tente de novo.");
  };

  Checkpoint.ano = function (dataIso) {
    return String(dataIso || "").slice(0, 4);
  };

  /* Nota 0 na API significa "sem nota". */
  Checkpoint.formatarNota = function (nota) {
    return Number(nota) > 0 ? Number(nota) + "/10" : "SEM NOTA";
  };

  Checkpoint.formatarTempo = function (minutos) {
    const total = Number(minutos) || 0;
    const horas = Math.floor(total / 60);
    const resto = total % 60;
    if (!horas) return resto + "min";
    return resto ? horas + "h " + resto + "min" : horas + "h";
  };

  Checkpoint.rotuloStatus = function (status) {
    const rotulos = {
      planejado: "Planejado",
      jogando: "Jogando",
      pausado: "Pausado",
      abandonado: "Abandonado",
      concluido: "Concluído",
    };
    return rotulos[status] || status;
  };
})();
