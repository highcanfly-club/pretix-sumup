/* © Ronan LE MEILlAT 2023 */
function waitForElm(selector) {
    return new Promise(resolve => {
        if (document.querySelector(selector)) {
            return resolve(document.querySelector(selector));
        }

        const observer = new MutationObserver(mutations => {
            if (document.querySelector(selector)) {
                resolve(document.querySelector(selector));
                observer.disconnect();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    });
}

waitForElm("#input_payment_sumuppayment").then((elm) => {
    console.log('Element #input_payment_sumuppayment is ready');
    elm.addEventListener("click", function(){
        alert("click");
      });
});