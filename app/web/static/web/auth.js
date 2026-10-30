(function () {
  const form = document.getElementById("form-auth");
  const dialogo = document.getElementById("dialogo");
  const botao = form.querySelector("button[type=submit]");
  const textoBotao = botao.textContent;

  async function chamarApi(url, corpo) {
    const resposta = await fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(corpo),
    });
    let dados = {};
    try {
      dados = await resposta.json();
    } catch (e) {
      /* resposta sem corpo JSON */
    }
    return { ok: resposta.ok, status: resposta.status, dados };
  }

  function limparErros() {
    dialogo.hidden = true;
    dialogo.textContent = "";
    form.querySelectorAll("[data-erro-para]").forEach((el) => (el.textContent = ""));
    form.querySelectorAll("input").forEach((el) => el.removeAttribute("aria-invalid"));
  }

  function mostrarDialogo(mensagem) {
    dialogo.textContent = mensagem;
    dialogo.hidden = false;
  }

  function mostrarErro(resposta) {
    const { status, dados } = resposta;
    if (status === 400) {
      let algumCampo = false;
      Object.entries(dados).forEach(([campo, mensagens]) => {
        const alvo = form.querySelector('[data-erro-para="' + campo + '"]');
        if (!alvo) return;
        algumCampo = true;
        alvo.textContent = [].concat(mensagens).join(" ");
        form.elements[campo].setAttribute("aria-invalid", "true");
      });
      if (!algumCampo) mostrarDialogo("Confira os dados informados.");
      return;
    }
    mostrarDialogo(dados.mensagem || "Algo deu errado. Tente de novo.");
  }

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    limparErros();
    botao.disabled = true;
    botao.textContent = "CARREGANDO...";

    const campos = Object.fromEntries(new FormData(form));
    try {
      if (form.dataset.acao === "cadastro") {
        const cadastro = await chamarApi("/api/usuarios/", campos);
        if (!cadastro.ok) return mostrarErro(cadastro);
      }
      const login = await chamarApi("/api/auth/login/", {
        email: campos.email,
        senha: campos.senha,
      });
      if (!login.ok) return mostrarErro(login);
      window.location.href = "/";
    } catch (e) {
      mostrarDialogo("Sem conexão com o servidor.");
    } finally {
      botao.disabled = false;
      botao.textContent = textoBotao;
    }
  });
})();
