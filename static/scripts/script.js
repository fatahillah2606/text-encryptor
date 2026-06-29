// Toggle menu
const navrail = document.getElementById("navrail");
if (navrail) {
    const railMenuList = navrail.querySelectorAll("a");
    const railfab = navrail.querySelector("md-fab");

    const menuBtn = document.getElementById("menu-btn");
    const menuIcon = menuBtn.querySelector("md-icon");
    const mainCont = document.querySelector("main");

    // For the ripple effect
    railMenuList.forEach((menu) => {
        const ripple = menu.querySelector("md-ripple");
        if (ripple) {
            ripple.attach(menu);
        }
    });

    // Extend menu
    function extendMenu() {
        mainCont.classList.remove("md:grid-cols-[96px_1fr]");
        mainCont.classList.add("md:grid-cols-[220px_1fr]");

        menuIcon.textContent = "menu_open";

        // Extend the menu list
        navrail.classList.add("extend");

        railMenuList.forEach((menu) => {
            // Remove
            menu.classList.remove("flex-col");
            menu.classList.remove("gap-1");
            menu.classList.remove("w-20");
            menu.querySelector("#rail-menu-ripple").classList.remove("hidden");

            // Add
            menu.classList.add("gap-0");
            menu.classList.add("rounded-full");
            menu.classList.add("w-fit");
            menu.classList.add("pr-5");
            menu.classList.add("ml-3");
            menu.querySelector("md-ripple").classList.add("hidden");
        });

        if (railfab) {
            railfab.setAttribute("label", "Add");
        }
    }

    // Shrink menu
    function shrinkMenu() {
        mainCont.classList.add("md:grid-cols-[96px_1fr]");
        mainCont.classList.remove("md:grid-cols-[220px_1fr]");

        menuIcon.textContent = "menu";

        // Shrink the menu list
        navrail.classList.remove("extend");

        railMenuList.forEach((menu) => {
            // Remove
            menu.classList.remove("rounded-full");
            menu.classList.remove("gap-0");
            menu.classList.remove("w-fit");
            menu.classList.remove("pr-5");
            menu.classList.remove("ml-3");
            menu.querySelector("md-ripple").classList.remove("hidden");

            // Add
            menu.classList.add("flex-col");
            menu.classList.add("gap-1");
            menu.classList.add("w-20");
            menu.querySelector("#rail-menu-ripple").classList.add("hidden");
        });

        if (railfab) {
            railfab.removeAttribute("label");
        }
    }

    // Menu btn listener
    menuBtn.addEventListener("click", () => {
        if (mainCont.classList.contains("md:grid-cols-[96px_1fr]")) {
            extendMenu();
        } else {
            shrinkMenu();
        }
    });
}

// Profile menu
const userProfile = document.body.querySelector("#user-profile");
const profileMenu = document.body.querySelector("#profile-menu");
if (userProfile) {
    userProfile.addEventListener("click", () => {
        profileMenu.open = !profileMenu.open;
    });
}

// Select option menu
const moreSelectOpt = document.body.querySelector("#more-select-opt");
const moreSelectMenu = document.body.querySelector("#more-select-menu");
if (moreSelectOpt) {
    moreSelectOpt.addEventListener("click", () => {
        moreSelectMenu.open = !moreSelectMenu.open;
    });
}

// Move page
function movePage(uri) {
    location.href = uri;
}

// Snackbar
let autoDismis;
function showSnackbar(message, action = null) {
    clearTimeout(autoDismis);
    const snackbar = document.querySelector("#snackbar");
    const fab = document.querySelector("md-fab");

    if (snackbar) {
        // Check if a FAB exists and is visible
        if (fab) {
            snackbar.classList.add("bottom-40");
        } else {
            snackbar.classList.remove("bottom-40");
        }

        const supportingText = snackbar.querySelector(
            "#snackbar-supporting-text",
        );
        const snackbarAction = snackbar.querySelector("#snackbar-action");

        supportingText.textContent = message;

        if (action) {
            try {
                snackbarAction.textContent = action.title;
                snackbarAction.setAttribute("onclick", action.action);

                snackbarAction.classList.remove("hidden");
            } catch (error) {
                console.error("Action must have 'title' and 'action'");
            }
        }

        // Animate showup
        snackbar.classList.remove("hidden");
        setTimeout(() => {
            snackbar.classList.remove("translate-y-5");
            snackbar.classList.remove("opacity-0");
        }, 50);

        autoDismis = setTimeout(() => {
            dismissSnackbar();
        }, 5000);
    } else {
        console.error("Snackbar element not found in this page!");
    }
}

function dismissSnackbar() {
    const snackbar = document.querySelector("#snackbar");

    if (snackbar) {
        // Animate dismis
        snackbar.classList.add("translate-y-5");
        snackbar.classList.add("opacity-0");
        setTimeout(() => {
            snackbar.classList.add("hidden");
            snackbar.querySelector("#snackbar-action").classList.add("hidden");
        }, 300);
    } else {
        console.error("Snackbar element not found in this page!");
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

            showSnackbar("Text copied.");
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

            showSnackbar("Text copied.");
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

    showSnackbar("Encryption key has been set.");
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
    const clearField = searchBar.querySelector("#clear-btn");

    searchField.addEventListener("keyup", () => {
        const searchValue = searchField.value.toLowerCase();

        // if search field not empty
        searchValue != ""
            ? clearField.classList.remove("hidden")
            : clearField.classList.add("hidden");

        filterSearch(searchValue);
    });

    // Hide clear field btn onclick
    clearField.addEventListener("click", () => {
        clearField.classList.add("hidden");
        const searchValue = "";

        filterSearch(searchValue);
    });
}

function filterSearch(search_value) {
    // If on the Password Page
    if (
        typeof allPasswords !== "undefined" &&
        document.getElementById("data_list") === pwList
    ) {
        passwordSearchQuery = search_value;
        renderPasswords();
    }
    // If on the Encryption Keys Page
    else if (
        typeof allKeys !== "undefined" &&
        document.getElementById("data_list") === keyList
    ) {
        keySearchQuery = search_value;
        renderKeys();
    }
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
