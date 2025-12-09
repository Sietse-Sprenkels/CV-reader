import base64
import io
from dash import Dash, html, dcc, Input, Output, callback, dash_table
import pandas as pd

from agent import ReadFailure, agent
from utils.pdf import PDFFile


app = Dash()
files: list[PDFFile] = []

candidatastes_df = pd.DataFrame(
    columns=[
        "name",
        "birth_date",
        "gender",
        "email",
        "phone_number",
        "linkedin_profile",
        "university",
        "study",
        "msc_start_date",
        "msc_graduation_date",
        "current_employer",
    ]
)

candidatastes_df.loc[0] = [
    "name",
    "01-01-1990",
    "male",
    "name@example.com",
    "1234567890",
    "linkedin.com/in/name",
    "University of Example",
    "Computer Science",
    "01-09-2015",
    "01-06-2017",
    "Example Corp",
]

app.layout = html.Div(
    [
        html.Div(
            [
                html.H1("Sprenkels AI", className="app-header"),
            ],
            className="navbar",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H2(
                            "Welke CV's wil je uitlezen?", className="upload-header"
                        ),
                        html.Div(
                            [
                                dcc.Upload(
                                    id="upload-data",
                                    className="upload-box",
                                    children=[
                                        html.Div(
                                            [
                                                "Sleep of ",
                                                html.A("selecteer pdf bestanden"),
                                            ],
                                            className="upload-instructions",
                                        ),
                                    ],
                                    accept=".pdf",
                                    multiple=True,
                                ),
                                html.Button(
                                    "Lezen",
                                    id="process-button",
                                ),
                            ],
                            className="upload-area",
                        ),
                    ],
                    className="upload-section",
                ),
                html.Div(id="upload-contents", className="output-container"),
                html.Div(
                    id="output-container",
                    className="output-container",
                ),
            ],
            className="main-content",
        ),
    ],
    className="container",
)


def parse_contents(contents: str) -> io.BytesIO:
    content_type, content_string = contents.split(",")
    if "pdf" not in content_type:
        raise ValueError("Unsupported file type. Please upload a PDF.")

    decoded = base64.b64decode(content_string)
    f = io.BytesIO(decoded)

    return f


@callback(
    Output("upload-contents", "children"),
    Input("upload-data", "filename"),
    Input("upload-data", "contents"),
)
def update_filenames(filenames, contents):
    if filenames is not None and contents is not None:
        files.extend(
            [
                PDFFile(filename, parse_contents(content))
                for filename, content in zip(filenames, contents)
            ]
        )
        return html.Ul([html.Li(html.P(file.filename)) for file in files])
    return "Nog geen bestanden geüpload."


@callback(
    Output("output-container", "children"),
    Input("process-button", "n_clicks"),
)
def process_pdfs(n_clicks):
    if n_clicks is None or not files:
        global candidatastes_df

        return html.Div()

    cv_texts = ""
    for pdf_file in files:
        cv_texts += f"[BEGIN CV]\n{pdf_file.content}\n[END CV]\n"

    result = agent.run_sync(cv_texts)

    if isinstance(result.output, ReadFailure):
        return html.Div(
            [
                html.H3("Read Failure"),
                html.P(result.output.explanation),
            ]
        )
    else:
        candidatastes = result.output
        candidatastes_df = pd.DataFrame(
            [candidate.model_dump() for candidate in candidatastes]
        )

        return (
            dash_table.DataTable(
                id="candidates-table",
                columns=[{"name": "kandidaat", "id": "Field"}]
                + [{"name": str(i + 1), "id": str(i)} for i in candidatastes_df.index],
                data=candidatastes_df.T.reset_index()
                .rename(columns={"index": "Field"})
                .to_dict("records"),
                style_cell={"textAlign": "left"},
                style_data={"backgroundColor": "rgb(66, 66, 66)"},
                style_header={"backgroundColor": "rgb(30, 30, 30)"},
            ),
        )


if __name__ == "__main__":
    # cv_texts = read_pdfs_from_dir("input")
    # result = agent.run_sync(cv_texts)
    # print(result.output)
    app.run(debug=True)
