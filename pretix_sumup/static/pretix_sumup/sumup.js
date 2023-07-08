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
function radioClickHandler() {
    let submitElm = document.querySelector('button[type="submit"]');
    if(document.querySelector("#input_payment_sumuppayment").checked){
        submitElm.classList.add('hidden');
        SumUpCard.mount({
            id: 'sumup-card',
            checkoutId: '2ceffb63-cbbe-4227-87cf-0409dd191a98',
            onResponse: function (type, body) {
              console.log('Type', type);
              console.log('Body', body);
            },
          });
    }else{
        submitElm.classList.remove('hidden');
    }
}

waitForElm("#input_payment_sumuppayment").then((sumupElm) => {
    console.log('Element #input_payment_sumuppayment is ready');
    waitForElm('button[type="submit"]').then((submitElm) => {
        console.log('Submit is ready');
        document.querySelectorAll('input[type="radio"]').forEach((radioElm) => {
            console.log(`add listener for ${radioElm}`);
            radioElm.parentElement.addEventListener("click", radioClickHandler);
        })
    })
});