// Toast
let autoDismis;
function showToast(message) {
    clearTimeout(autoDismis);
    const toast = document.querySelector("#toast-default");

    if (toast) {
        const toastMessage = toast.querySelector("#toast-message");

        toastMessage.textContent = message;
        toast.classList.remove("hidden");

        autoDismis = setTimeout(() => {
            dismisToast();
        }, 5000);
    } else {
        console.error("Toast element not found in this page!");
    }
}

function dismisToast() {
    const toast = document.querySelector("#toast-default");

    if (toast) {
        toast.classList.add("hidden");
    } else {
        console.error("Toast element not found in this page!");
    }
}

// Copy text
function copyText(field) {
    const fieldId = document.getElementById(field);

    fieldId.select();
    fieldId.setSelectionRange(0, 99999); // For mobile devices

    navigator.clipboard.writeText(fieldId.value);

    showToast("Text copied.");
}

// Show password
function showPassword(elmClicked, elmPassword) {
    const passwordField = document.getElementById(elmPassword);

    if (passwordField.type == "password") {
        passwordField.type = "text";
        elmClicked.textContent = "visibility_off";
    } else {
        passwordField.type = "password";
        elmClicked.textContent = "visibility";
    }
}

function showPasswordCheckBox(elmCheckBox, elmPasswords) {
    const passwordField = [];

    // Get all password elm
    elmPasswords.forEach((elm) => {
        passwordField.push(document.getElementById(elm));
    });

    // Change all password type
    passwordField.forEach((elm) => {
        if (elmCheckBox.checked) {
            elm.type = "text";
        } else {
            elm.type = "password";
        }
    });
}

// Increase value
function increaseValue(field) {
    const numField = document.getElementById(field);
    let value = parseInt(numField.value, 10);

    value = isNaN(value) ? 0 : value;
    value++;

    numField.value = value;
}

function decreaseValue(field) {
    const numField = document.getElementById(field);
    let value = parseInt(numField.value, 10);

    value = isNaN(value) ? 0 : value;
    if (value > 0) {
        value--;
    }

    numField.value = value;
}

// Supporting text
function showSupportText(elm, message) {
    elm.textContent = message;
    elm.classList.remove("hidden");
}

function hideSupportText(elm) {
    elm.classList.add("hidden");
}

// auto generate key
async function generateAndSetKey() {
    const data = await generateEncryptionKey();
    saveKeyToSession(data);
}

// Set manual key
const key_api_uri = "/api/encryptor/encryption_key";
async function setEncryptionKey(theKey) {
    try {
        data = { key: theKey };
        const result = await sendRequest(key_api_uri, data, "POST");

        keyData = {
            key_name: "manual",
            encryption_key: result.data.key,
        };

        saveKeyToSession(keyData);
    } catch (error) {
        showToast(error);
        console.error(error);
    }
}

// Save encryption key to session storage
function saveKeyToSession(data) {
    keyData = { name: data.key_name, key: data.encryption_key };
    sessionStorage.setItem("encryption_key", JSON.stringify(keyData));

    showToast("Encryption key has been set.");
    checkEncryptionKey();
}

// logout
function logout() {
    sessionStorage.clear();
    location.href = "/pages/logout";
}
