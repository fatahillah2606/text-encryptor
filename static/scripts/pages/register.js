// Prograss bar
const progressBar = document.querySelector("md-linear-progress");

/* ========== Field validity ========== */
const allField = document.querySelectorAll("md-outlined-text-field");

function checkFieldValidity(fields) {
    let accountValid = true;
    fields.forEach((field) => {
        if (!field.checkValidity()) {
            showSupportText(field, "Please fill out this field.");

            accountValid = false;
        }
    });

    return accountValid;
}

// Remove all error sign
allField.forEach((field) => {
    field.addEventListener("keyup", () => {
        if (field.value.length > 0) {
            hideSupportText(field);
        }
    });
});

/* ========== Slide animation ========== */
const slider = document.querySelector("#slider");

async function slideNext() {
    registerForm.next_step.disabled = true;
    // Check validity before going to next step
    const accountContent = document.querySelectorAll(
        "#account-content md-outlined-text-field",
    );

    const usernameField = accountContent[1];
    let accountValid = checkFieldValidity(accountContent);

    // Check availablity of username
    if (accountValid) {
        // Make sure to remove supporting text first
        hideSupportText(usernameField);

        // Api uri for check availablity
        username_api = "/api/account/username/available";

        try {
            progressBar.classList.remove("hidden");

            // data
            const data = { username: usernameField.value };

            // Send request
            const result = await sendRequest(username_api, data, "POST");

            // If username available
            if (result.code == 200) {
                progressBar.classList.add("hidden");
                registerForm.next_step.disabled = false;
                slider.style.transform = "translateX(-100%)";
            }
        } catch (error) {
            // If unavailable
            progressBar.classList.add("hidden");
            registerForm.next_step.disabled = false;

            showSupportText(usernameField, error.message);
        }
    } else {
        registerForm.next_step.disabled = false;
    }
}

function slidePrev() {
    slider.style.transform = "translateX(0)";
}

/* ========== Auth ========== */
const regist_api = "/api/auth/register";
const registerForm = document.getElementById("register_form");
const retypePw = document.querySelector("#retype_password");

async function register(formulir) {
    try {
        progressBar.classList.remove("hidden");

        // Aquired data
        let formData = new FormData(formulir);
        formData = Object.fromEntries(formData.entries());

        // Send request
        const result = await sendRequest(regist_api, formData, "POST");

        if (result.code === 200) {
            progressBar.classList.add("hidden");
            registerForm.register.disabled = false;
            location.href = "/pages/home";
        }
    } catch (error) {
        progressBar.classList.add("hidden");
        registerForm.register.disabled = false;

        showAlert("Unable to register you", error.message);
    }
}

registerForm.addEventListener("submit", (event) => {
    event.preventDefault();

    if (registerForm.register.disabled === false) {
        registerForm.register.disabled = true;

        // Check all field validity
        let valid = checkFieldValidity(allField);

        if (valid) {
            if (
                registerForm.password.value ===
                registerForm.retype_password.value
            ) {
                register(registerForm);
            } else {
                registerForm.register.disabled = false;
                showSupportText(
                    retypePw,
                    "The password does not match. Please try again.",
                );
            }
        }
    }
});
