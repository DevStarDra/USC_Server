from threading import Thread
from typing import Union

from CFR.models import CFRNode, CFRNodeManager
from django.conf import settings
from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_page
from USCODE.models import Node, NodeManager
from utils.ai_query import ai_query
from django.views.generic import TemplateView
from django.contrib import messages
from utils.general import remove_session

QA = "QA"


@cache_page(5)
def index(request):
    """Show collections available"""
    context = {
        "collections": [
            {
                "name": "CFR - Code of Federal Regulations",
                "code": settings.CFR,
            },
            {
                "name": "USCS - United States Code Service",
                "code": settings.USCODE,
            },
        ]
    }
    return render(request, 'Main/index.html', context)


def update_cookies(request):
    if request.POST:
        accept = request.POST.get('accept')
        if accept == 'true':
            remove_session(request, settings.DISABLE_COOKIES)
            messages.success(request, "Cookies enabled")
            return redirect(request.META.get("HTTP_REFERER", "/"))
        elif accept == 'false':
            request.session[settings.DISABLE_COOKIES] = True
            messages.success(request, "Cookies disabled")
            return redirect(request.META.get("HTTP_REFERER", "/"))

    return redirect(request.META.get("HTTP_REFERER", "/"))


def make_qa(query: str):
    return ai_query(query).lstrip("?")


def get_qa(query, datax: dict):
    try:
        qa = make_qa(query)
    except Exception:
        qa = "Error generating answer"
    datax["qa"] = qa


def get_cfr(query, datax: dict):
    cfr_results = CFRNode.objects.full_text_search(query)
    datax["cfr"] = cfr_results


def get_usc(query, datax: dict):
    usc_results = Node.objects.full_text_search(query)
    datax["usc"] = usc_results


AI_TERM_SESSION_KEY = "ai_term_accepted"


class FullTextSearch(TemplateView):
    template_name = "Main/search.html"

    def get(self, request, *args, **kwargs):
        context = {}

        display_qa = True

        # check if user has accepted cookies
        if request.session.get(settings.DISABLE_COOKIES):
            messages.warning(
                request,
                'Please enable cookies to get the best \
experience using this site. You can disable cookies later.')
            display_qa = False

        # Check if the user as accepted AI generated answers term
        context[AI_TERM_SESSION_KEY] = request.session.get(
            AI_TERM_SESSION_KEY, False)

        query = request.GET.get("search")
        collection = request.GET.get("collection")

        if query:
            if collection == '':
                datax = {
                    "usc": None,
                    "cfr": None,
                    "qa": None
                }

                # Run all searches in parallel
                threads = [
                    Thread(target=get_cfr, args=(query, datax)),
                    Thread(target=get_usc, args=(query, datax)),
                ]
                if (context[AI_TERM_SESSION_KEY] and display_qa):
                    threads.append(Thread(target=get_qa, args=(query, datax)))

                for thread in threads:
                    thread.start()

                for thread in threads:
                    thread.join()

                usc_results = datax["usc"]
                cfr_results = datax["cfr"]
                qa = datax["qa"]

                # Combine results of separate model arranged 5 each in a list
                results = []
                for i in range(0, max(len(usc_results), len(cfr_results)), 5):
                    results.extend(usc_results[i:i+5])
                    results.extend(cfr_results[i:i+5])

                context.update({
                    "nodes": results,
                    "qa": qa
                })

            elif (collection == QA) \
                    and (context[AI_TERM_SESSION_KEY] and display_qa):
                context.update({
                    "qa": make_qa(query)
                })

            else:
                COLLECTION: dict[str, Union[NodeManager, CFRNodeManager]] = {
                    settings.USCODE: Node.objects,
                    settings.CFR: CFRNode.objects,
                }

                main = COLLECTION.get(collection)
                if main:
                    context['nodes'] = main.full_text_search(query)
        return self.render_to_response(context)

    def post(self, *args, **kwargs):
        # Accept the AI generated answers term
        if self.request.POST.get("accept_ai_terms"):
            self.request.session[AI_TERM_SESSION_KEY] = True
        # Redirect to the same page
        redirect_url = self.request.META.get("HTTP_REFERER", "/")
        return redirect(redirect_url)
