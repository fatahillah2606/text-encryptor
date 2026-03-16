// Send request
function sendRequest(apiURI, data = null, methodType = "GET") {
    // Set request init
    const requestInit = {
        method: methodType,
        headers: { "Content-Type": "application/json" },
    };

    // If method is POST or PUT, attach the body
    if (methodType !== "GET" && methodType !== "DELETE" && data) {
        requestInit.body = JSON.stringify(data);
    }

    // Send request
    return new Promise((resolve, reject) => {
        fetch(apiURI, requestInit)
            .then(async (response) => {
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(
                        data.message || `Failed to fetch API: ${apiURI}`,
                    );
                }
                return data;
            })
            .then((data) => {
                resolve(data);
            })
            .catch((error) => {
                reject(error);
            });
    });
}
