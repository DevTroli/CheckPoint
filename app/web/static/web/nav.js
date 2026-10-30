(async function () {
  const alvo = document.getElementById("menu-usuario");
  if (!alvo) return;

  const usuario = await Checkpoint.usuario();
  if (!usuario) return; // mantém os links Entrar/Cadastrar do HTML

  const sair = Checkpoint.el("button", { type: "button", class: "link-botao" }, "Sair");
  sair.addEventListener("click", async () => {
    await Checkpoint.api("POST", "/api/auth/logout/");
    window.location.href = "/entrar/";
  });

  alvo.replaceChildren(Checkpoint.el("span", { class: "jogador" }, usuario.nome_usuario), sair);
})();
