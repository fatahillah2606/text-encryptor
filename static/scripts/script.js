// Toast
function showToast(message) {
    const toast = document.querySelector("#toast-default");
    if (toast) {
        const toastMessage = toast.querySelector("#toast-message");
        toastMessage.textContent = message;
        toast.classList.remove("hidden");
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

function copyText(field) {
    const fieldId = document.getElementById(field);

    fieldId.select();
    fieldId.setSelectionRange(0, 99999); // For mobile devices

    navigator.clipboard.writeText(fieldId.value);

    showToast("Text copied.");
}

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
