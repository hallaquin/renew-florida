// URL base del backend propio de Renew Florida.
// En desarrollo local, corre el backend con `flask --app backend.app run` y deja localhost:5000.
// En producción, reemplaza esto con la URL pública del servicio (Railway/Render) una vez desplegado.
const API_BASE_URL = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
    ? "http://localhost:5000"
    : "https://renew-florida-production.up.railway.app";
