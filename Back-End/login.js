function mostrarSenha() {
  const input = document.getElementById("box2");
  if (input.type === "password") {
    input.type = "text";
  } else {
    input.type = "password";
  }
}