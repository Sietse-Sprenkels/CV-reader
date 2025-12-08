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
                html.H1("CV Reader", className="app-header"),
            ],
            className="navbar",
        ),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Upload(
                            id="upload-data",
                            className="upload-box",
                            children=html.Div(
                                ["Drag and Drop or ", html.A("Select PDF Files")]
                            ),
                            multiple=True,
                        ),
                        html.Button(
                            "GO!",
                            id="process-button",
                        ),
                    ],
                    className="upload-container",
                ),
                html.Div(id="upload-contents", className="output-container"),
                dash_table.DataTable(
                    id="candidates-table",
                    columns=[{"name": "", "id": "Field"}]
                    + [
                        {"name": candidatastes_df.loc[i, "name"], "id": str(i)}
                        for i in candidatastes_df.index
                    ],
                    data=candidatastes_df.T.reset_index()
                    .rename(columns={"index": "Field"})
                    .to_dict("records"),
                    style_cell={"textAlign": "left"},
                    style_data={"backgroundColor": "#D9D9D9"},
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
    return "No files uploaded yet."


@callback(
    Output("candidates-table", "data"),
    Output("candidates-table", "columns"),
    Input("process-button", "n_clicks"),
)
def process_pdfs(n_clicks):
    if n_clicks is None or not files:
        global candidatastes_df
        return (
            candidatastes_df.T.reset_index()
            .rename(columns={"index": "Field"})
            .to_dict("records"),
            [{"name": "", "id": "Field"}]
            + [
                {"name": candidatastes_df.loc[i, "name"], "id": str(i)}
                for i in candidatastes_df.index
            ],
        )

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
            candidatastes_df.T.reset_index()
            .rename(columns={"index": "Field"})
            .to_dict("records"),
            [{"name": "", "id": "Field"}]
            + [
                {"name": candidatastes_df.loc[i, "name"], "id": str(i)}
                for i in candidatastes_df.index
            ],
        )


if __name__ == "__main__":
    # cv_texts = read_pdfs_from_dir("input")
    # result = agent.run_sync(cv_texts)
    # print(result.output)
    app.run(debug=True)
