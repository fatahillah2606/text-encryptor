// ========== Sliding animation ==========
const slider = document.querySelector("#slider");
let account = null;

function slideNext(selectedAccount) {
    account = selectedAccount;
    slider.style.transform = "translateX(-100%)";
}

function slidePrev() {
    account = null;
    slider.style.transform = "translateX(0)";
}

// ========== Auth ==========
const login_api = "/api/auth/login";
const loginForm = document.getElementById("login_form");
const theField = document.querySelector("#password");

async function login(formulir) {
    // Prograss bar
    const progressBar = document.querySelector("md-linear-progress");

    try {
        progressBar.classList.remove("hidden");

        // Aquired data
        let formData = new FormData(formulir);
        formData.append("username", account);

        formData = Object.fromEntries(formData.entries());

        // Send request
        const result = await sendRequest(login_api, formData, "POST");

        if (result.code === 200) {
            loginForm.login.disabled = false;

            progressBar.classList.add("hidden");
            location.href = "/pages/dashboard";
        }
    } catch (error) {
        progressBar.classList.add("hidden");
        loginForm.login.disabled = false;

        showSupportText(theField, error.message);
    }
}

loginForm.addEventListener("submit", (event) => {
    event.preventDefault();

    if (loginForm.login.disabled === false) {
        loginForm.login.disabled = true;
        hideSupportText(theField);
        login(loginForm);
    }
});
