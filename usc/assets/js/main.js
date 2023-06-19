
// Make sure when users click decline, they are redirected to the homepage
function disableCookies() {
    // disable cookies
    $("#cookieForm input[name='accept']").val("false");
    $("#cookieForm").submit();
}

function enableCookies() {
    // enable cookies
    $("#cookieForm input[name='accept']").val("true");
    $("#cookieForm").submit();
}

window.addEventListener("load", function () {
    window.cookieconsent.initialise({
        "palette": {
            "popup": {
                "background": "#ffe5e5",
                "text": "#050510"
            },
            "button": {
                "background": "#fd2b3c"
            }
        },
        "theme": "classic",
        "position": "bottom-left",
        "type": "opt-in",
        "content": {
            "href": "/privacy-policy/"
        },
        onStatusChange: function (status, chosenBefore) {
            var type = this.options.type;
            var didConsent = this.hasConsented();

            if (type == 'opt-in' && didConsent) {
                // enable cookies
                enableCookies()
            }

            if (type == 'opt-in' && !didConsent) {
                // disable cookies
                disableCookies()
            }
        },
    })
});


/* ---- particles.js config ---- */
particlesJS("particles-js", {
    "particles": {
        "number": {
            "value": 380,
            "density": {
                "enable": true,
                "value_area": 800
            }
        },
        "color": {
            "value": "#fd2b3c"
        },
        "shape": {
            "type": "circle",
            "stroke": {
                "width": 0,
                "color": "#d6144f"
            },
            "polygon": {
                "nb_sides": 5
            },
            "image": {
                "src": "img/github.svg",
                "width": 100,
                "height": 100
            }
        },
        "opacity": {
            "value": .5,
            "random": false,
            "anim": {
                "enable": false,
                "speed": 1,
                "opacity_min": 0.1,
                "sync": false
            }
        },
        "size": {
            "value": 5,
            "random": true,
            "anim": {
                "enable": false,
                "speed": 20,
                "size_min": 0.1,
                "sync": false
            }
        },
        "line_linked": {
            "enable": true,
            "distance": 150,
            "color": "#000",
            "opacity": 0.4,
            "width": 1
        },
        "move": {
            "enable": true,
            "speed": 5,
            "direction": "none",
            "random": true,
            "straight": false,
            "out_mode": "bounce",
            "bounce": false,
            "attract": {
                "enable": false,
                "rotateX": 600,
                "rotateY": 1200
            }
        }
    },
    "interactivity": {
        "detect_on": "window",
        "events": {
            "onhover": {
                "enable": true,
                "mode": "grab"
            },
            "onclick": {
                "enable": true,
                "mode": "push"
            },
            "resize": true
        },
        "modes": {
            "grab": {
                "distance": 140,
                "line_linked": {
                    "opacity": 1
                }
            },
            "bubble": {
                "distance": 400,
                "size": 40,
                "duration": 2,
                "opacity": 8,
                "speed": 3
            },
            "repulse": {
                "distance": 200,
                "duration": 0.4
            },
            "push": {
                "particles_nb": 4
            },
            "remove": {
                "particles_nb": 2
            }
        }
    },
    "retina_detect": true
});


// Codes for ajax setup for get and post requests to backend
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        let cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            let cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


let csrftoken = getCookie('csrftoken');


function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}


try {
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
} catch (e) {
    console.error(e)
}


function submit_query() {
        let aiQueryInput = document.querySelector('#ai-query-input');
        if (aiQueryInput.value == '') {
            alert('No query input found')
            return
        }

        let data = {
            'query': aiQueryInput.value
        }

        let thisURL = "/query/"
        let resultDiv = document.querySelector('#ai-result');

        let errorCallback = function () {
            alert("No result found, please try to contact us");
            resultDiv.classList.add('d-none');
            resultDiv.innerHTML = '';
        }

        $.ajax({
            method: "POST",
            url: thisURL,
            data: data,
            success: function (data) {
                let result = data['result'];

                if (result == '' || result.endsWith('Unknown.')) {
                    errorCallback();
                    return
                }

                resultDiv.classList.remove('d-none');
                resultDiv.innerHTML = result;
            },
            error: function () {
                errorCallback();
            },
        })

}

if ($('#submit-ai-query').length) {
    $('#submit-ai-query').click(function(){
        submit_query()
    })
}
