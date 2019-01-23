(() => {
    window.addEventListener('load', () => {

        const POST = document.querySelector('#post-article')
        const DOMAIN =  window.location.origin

        console.log(DOMAIN)

        if (POST) {
            const SESSION_ID = POST.dataset.sessionId
            console.log(POST)

            if (SESSION_ID !== 'null') {
                let minutes = 0
                setInterval(() => {
                    let form = new FormData()
                    minutes = minutes + 1
                    form.append('minutes', minutes)
                    const URI = `${DOMAIN}/posts/interaction/${SESSION_ID}/edit/`
                    console.log(URI)
                    fetch(URI, {
                        method: 'post',
                        body: form
                    })
                        .then(response => response.json())
                        .then(response => console.log(response))
                }, (60 * 1000))
            }
        }
    })
})()