// Move page
function movePage(uri) {
    location.href = uri;
}

// Toast
let autoDismis;
function showToast(message) {
    clearTimeout(autoDismis);
    const toast = document.querySelector("#toast-default");
    const fab = document.querySelector("md-fab");

    if (toast) {
        // Check if a FAB exists and is visible
        if (fab) {
            toast.classList.add("bottom-24");
        } else {
            toast.classList.remove("bottom-24");
        }

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

// Alert dialog
async function showAlert(headline, content) {
    const dialog = document.getElementById("alert-dialog");

    if (dialog) {
        dialog.querySelector('[slot="headline"]').innerText = headline;
        dialog.querySelector("form").innerText = content;

        await dialog.show();
    } else {
        console.error("Alert dialog not found in this page!");
    }
}

// Copy text
function copyText(field, copyBtn) {
    const element = document.getElementById(field);
    if (!element) return;

    // Grab text depending on the element type
    const text =
        element.value !== undefined ? element.value : element.innerText;

    navigator.clipboard
        .writeText(text)
        .then(() => {
            copyBtn.textContent = "Copied";
            copyBtn.disabled = true;

            setTimeout(() => {
                copyBtn.textContent = "Copy";
                copyBtn.disabled = false;
            }, 2000);

            showToast("Text copied.");
        })
        .catch((err) => {
            showAlert("Clipboard write failed.", err);
        });
}

function copyTextIconBtn(field, copyIconBtn, event) {
    event.preventDefault();

    const element = document.getElementById(field);
    if (!element) return;

    const copyIcon = copyIconBtn.querySelector("md-icon");

    // Grab text depending on the element type
    const text =
        element.value !== undefined ? element.value : element.innerText;

    navigator.clipboard
        .writeText(text)
        .then(() => {
            copyIcon.textContent = "check";
            copyIcon.disabled = true;

            setTimeout(() => {
                copyIcon.textContent = "content_copy";
                copyIcon.disabled = false;
            }, 1000);

            showToast("Text copied.");
        })
        .catch((err) => {
            showAlert("Clipboard write failed.", err);
        });
}

// Show password
function showPasswordCheckBox(elmCheckBox, elmPasswords) {
    // Get all password elm
    const passwordField = elmPasswords.map((id) => document.getElementById(id));

    // Change all password type
    passwordField.forEach((elm) => {
        if (elm) {
            elm.type = elmCheckBox.checked ? "text" : "password";
        }
    });
}

function showPw(checkboxId, fieldId) {
    const checkboxElm = document.getElementById(checkboxId);
    checkboxElm.addEventListener("change", (e) => {
        showPasswordCheckBox(e.target, fieldId);
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
    elm.error = true;
    elm.errorText = message;
}

function hideSupportText(elm) {
    elm.error = false;
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
        showAlert("Failed to set encryption key", error.message);
    }
}

// Generate key
async function generateKey(elmId) {
    try {
        const elm = document.querySelector(elmId);

        data = { key: "" };
        const result = await sendRequest(key_api_uri, data, "POST");

        elm.value = result.data.key;

        return true;
    } catch (error) {
        showAlert("Failed to generate encryption key", error.message);
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

// Confirm dialog
async function confirmDialog(dialogId, headline, content) {
    const dialog = document.getElementById(dialogId);
    dialog.querySelector('[slot="headline"]').innerText = headline;
    dialog.querySelector("form").innerText = content;

    dialog.show();

    return new Promise((resolve) => {
        dialog.addEventListener("closed", () => resolve(dialog.returnValue), {
            once: true,
        });
    });
}

// Search
const searchBar = document.getElementById("search-bar");

if (searchBar) {
    const searchField = searchBar.querySelector("input");

    searchField.addEventListener("keyup", () => {
        const searchValue = searchField.value.toLowerCase();

        const dataRow = document.querySelectorAll("#data_list > div");

        dataRow.forEach((data) => {
            let match = false;

            const h2Title = data.querySelectorAll("h2");
            const pBody = data.querySelectorAll("p");

            // For h2 elm
            if (h2Title.length !== 0) {
                h2Title.forEach((element) => {
                    if (
                        element.textContent.toLowerCase().includes(searchValue)
                    ) {
                        match = true;
                    }
                });
            }

            // For p elm
            if (pBody.length !== 0) {
                pBody.forEach((element) => {
                    if (
                        element.textContent.toLowerCase().includes(searchValue)
                    ) {
                        match = true;
                    }
                });
            }

            // If match
            if (match) {
                data.classList.remove("hidden");
            } else {
                data.classList.add("hidden");
            }
        });
    });
}

// Enable submit button only if all field is not empty
function requireAllFields(fields, submitBtn) {
    submitBtn.disabled = true;

    const validate = () => {
        fields.forEach((field) => {
            field.value.trim() !== ""
                ? (submitBtn.disabled = false)
                : (submitBtn.disabled = true);
        });
    };

    fields.forEach((field) => {
        field.addEventListener("input", validate);
    });
}

// Timestamp
function timeStamp() {
    const now = new Date();

    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");

    const hours = String(now.getHours()).padStart(2, "0");
    const minutes = String(now.getMinutes()).padStart(2, "0");
    const seconds = String(now.getSeconds()).padStart(2, "0");

    const timestamp = `${year}-${month}-${day} ${hours}-${minutes}-${seconds}`;
    return timestamp;
}

// Tempoary object url
function tempoaryUrl(blob, nameFile, fileType) {
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    const fileName = `${nameFile} ${timeStamp()}.${fileType}`;

    link.setAttribute("href", url);
    link.setAttribute("download", fileName);
    link.style.visibility = "hidden";

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}
