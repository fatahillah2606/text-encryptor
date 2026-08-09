// ========== Sliding animation ==========
const slider = document.querySelector("#slider");
let account = null;
let currentIndex = 0;

function updatePosition() {
    slider.style.transform = `translateX(-${currentIndex * 100}%)`;
}

function slideNext(selectedAccount = null) {
    if (selectedAccount) {
        account = selectedAccount;
    }

    currentIndex++;
    updatePosition();
}

function slidePrev() {
    if (currentIndex === 0) {
        account = null;
    }
    currentIndex--;
    updatePosition();
}

// ========== Recovery ==========
const recovery_api = "/api/account/recovery";
const recoveryForm = document.getElementById("recovery_form");
const duplicateAction = document.getElementById("duplicate_action");

async function decryptAndRecover(formulir, duplicate_action = null) {
    // Prograss bar
    const progressBar = document.querySelector("md-linear-progress");

    progressBar.classList.remove("hidden");

    // Aquired data
    let formData = new FormData(formulir);
    formData.append("username", account);
    formData = Object.fromEntries(formData.entries());

    let action;
    if (duplicate_action) {
        action = new FormData(duplicate_action);
        action = Object.fromEntries(action.entries());
    }

    formData.action = action;

    // Send request
    sendRequest(recovery_api, formData, "POST")
        .then((response) => {
            if (response.code === 201) {
                const dataSheet = response.data;
                const blob = new Blob([dataSheet.json_file], {
                    type: "application/json;charset=utf-8;",
                });

                tempoaryUrl(blob, "Sunako - Keys & Passwords", "json");

                showSnackbar(response.message);
            } else {
                location.href = "/pages/dashboard";
            }

            recoveryForm.recover.disabled = false;
            duplicateAction.proceed.disabled = false;
            progressBar.classList.add("hidden");
        })
        .catch((error) => {
            if (error.code === 409 && currentIndex === 1) {
                slideNext();
            } else {
                // Password form
                if (currentIndex === 1) {
                    showSupportText(recoveryForm.password, error.message);
                }

                // Duplicate action form
                if (currentIndex === 2) {
                    showSupportText(duplicateAction.username, error.message);
                }
            }

            recoveryForm.recover.disabled = false;
            duplicateAction.proceed.disabled = false;
            progressBar.classList.add("hidden");
        });
}

// radio listener
const optionRadio = duplicateAction.option;
optionRadio.forEach((radio) => {
    radio.addEventListener("change", () => {
        if (duplicateAction.create_new_option.checked) {
            duplicateAction.username.disabled = false;
        } else {
            duplicateAction.username.disabled = true;
        }
    });
});

// Recovery form submit btn
recoveryForm.addEventListener("submit", (event) => {
    event.preventDefault();

    if (recoveryForm.recover.disabled === false) {
        recoveryForm.recover.disabled = true;

        hideSupportText(recoveryForm.password);
        decryptAndRecover(recoveryForm);
    }
});

// Duplicate action form submit btn
duplicateAction.addEventListener("submit", (event) => {
    event.preventDefault();

    if (duplicateAction.proceed.disabled === false) {
        duplicateAction.proceed.disabled = true;

        hideSupportText(duplicateAction.username);
        decryptAndRecover(recoveryForm, duplicateAction);
    }
});
