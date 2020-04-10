
import dash_html_components as html

FOOTER = html.Footer(
    html.Span(
        [
            "Sourcecode available on ",
            html.A(
                " s-weigand/covid19-data-analyzer",
                href="https://github.com/s-weigand/covid19-data-analyzer",
            ),
        ]
    ),
    className="source-link",
)
