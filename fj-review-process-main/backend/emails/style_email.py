"""This module contains the FJStyledEmail class, which is used to send styled emails to users."""

from emails.fjemail import send_email
from config import settings


class FJStyledEmail():

    def __init__(self,
                 From: str,
                 To: str | list[str],
                 Subject,
                 Title,
                 CC: str | list[str] | None = None,
                 BCC: str | list[str] | None = None,
                 Attachment=None,
                 AttachmentName=None):
        self.From = From
        self.To = To
        self.Subject = Subject
        self.Title = Title
        self.CC = CC
        if type(BCC) == str:
            self.BCC = [BCC] + settings.CODE_ADMIN_EMAILS
        elif type(BCC) == list[str]:
            self.BCC = BCC + settings.CODE_ADMIN_EMAILS
        else:
            self.BCC = settings.CODE_ADMIN_EMAILS

        self.Attachment = Attachment
        self.AttachmentName = AttachmentName
        self.message = ""
        self.text = ""

    def add_text(self, text):
        self.message += f"""\
            <p style="font-size: 16px; font-family: Arial, Helvetica, sans-serif; color: #ffffff; margin-top: 0; margin-bottom: 0;"
            >{text}</p>"""
        self.text += f"{text}\n"

    def add_link_button(self, text, link):
        self.message += f"""\
            <a href="{link}" target="_blank"><button
                                                    class="btn btn-primary"
                                                    style="margin-top: 20px; margin-bottom: 20px; background-color: #C3962C; border: none; color: #ffffff; padding: 12px 12px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; border-radius: 5px;">
                                                    {text}
                                                </button></a>
                                                """
        self.text += f"{text}: {link}\n"

    def send(self):
        self.body = self.generate_body()
        send_email(self.From, self.To, self.Subject,
                   self.body, self.CC, self.BCC, self.Attachment, self.AttachmentName)

    def generate_body(self) -> str:
        return """\
        <!doctype html>
<html>

<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <title>Simple Transactional Email</title>
    <style>
        /* -------------------------------------
          GLOBAL RESETS
      ------------------------------------- */

        /*All the styling goes here*/

        img {
            border: none;
            -ms-interpolation-mode: bicubic;
            max-width: 100%;
        }

        body {
            background-color: #263844;
            font-family: sans-serif;
            -webkit-font-smoothing: antialiased;
            font-size: 14px;
            line-height: 1.4;
            margin: 0;
            padding: 0;
            color: white;
            -ms-text-size-adjust: 100%;
            -webkit-text-size-adjust: 100%;
        }

        table {
            border-collapse: separate;
            mso-table-lspace: 0pt;
            mso-table-rspace: 0pt;
            width: 100%;
        }

        table td {
            font-family: sans-serif;
            font-size: 14px;
            vertical-align: top;
        }

        /* -------------------------------------
          BODY & CONTAINER
      ------------------------------------- */

        .body {
            background-color: #263844;
            width: 100%;
        }

        /* Set a max-width, and make it display as block so it will automatically stretch to that width, but will also shrink down on a phone or something */
        .container {
            display: block;
            margin: 0 auto !important;
            /* makes it centered */
            max-width: 580px;
            padding: 10px;
            width: 580px;
        }

        /* This should also be a block element, so that it will fill 100% of the .container */
        .content {
            box-sizing: border-box;
            display: block;
            margin: 0 auto;
            max-width: 580px;
            padding: 10px;
        }

        /* -------------------------------------
          HEADER, FOOTER, MAIN
      ------------------------------------- */
        .main {
            background: #263844;
            border-radius: 25px;
            border: 2px solid #C3962C;
            width: 100%;
            /* shadow around */
            box-shadow: 0 0 40px rgba(0, 0, 0, 0.2);
        }

        .wrapper {
            box-sizing: border-box;
            padding: 20px;
        }

        .content-block {
            padding-bottom: 10px;
            padding-top: 10px;
        }

        .footer {
            clear: both;
            margin-top: 10px;
            text-align: center;
            width: 100%;
        }

        .footer td,
        .footer p,
        .footer span,
        .footer a {
            color: white;
            font-size: 12px;
            text-align: center;
        }

        /* -------------------------------------
          TYPOGRAPHY
      ------------------------------------- */
        h1,
        h2,
        h3,
        h4 {
            color: #000000;
            font-family: sans-serif;
            font-weight: 400;
            line-height: 1.4;
            margin: 0;
            margin-bottom: 30px;
        }

        h1 {
            font-size: 35px;
            font-weight: 300;
            text-align: center;
            text-transform: capitalize;
        }

        p,
        ul,
        ol {
            font-family: sans-serif;
            font-size: 14px;
            font-weight: normal;
            margin: 0;
            margin-bottom: 15px;
        }

        p li,
        ul li,
        ol li {
            list-style-position: inside;
            margin-left: 5px;
        }

        a {
            color: #3498db;
            text-decoration: underline;
        }

        /* -------------------------------------
          BUTTONS
      ------------------------------------- */
        .btn {
            box-sizing: border-box;
            width: 100%;
        }

        .btn>tbody>tr>td {
            padding-bottom: 15px;
        }

        .btn table {
            width: auto;
        }

        .btn table td {
            background-color: #ffffff;
            border-radius: 5px;
            text-align: center;
        }

        .btn a {
            background-color: #ffffff;
            border: solid 1px #3498db;
            border-radius: 5px;
            box-sizing: border-box;
            color: #3498db;
            cursor: pointer;
            display: inline-block;
            font-size: 14px;
            font-weight: bold;
            margin: 0;
            padding: 12px 25px;
            text-decoration: none;
            text-transform: capitalize;
        }

        .btn-primary table td {
            background-color: #3498db;
        }

        .btn-primary a {
            background-color: #3498db;
            border-color: #3498db;
            color: #ffffff;
        }

        /* -------------------------------------
          OTHER STYLES THAT MIGHT BE USEFUL
      ------------------------------------- */
        .last {
            margin-bottom: 0;
        }

        .first {
            margin-top: 0;
        }

        .align-center {
            text-align: center;
        }

        .align-right {
            text-align: right;
        }

        .align-left {
            text-align: left;
        }

        .clear {
            clear: both;
        }

        .mt0 {
            margin-top: 0;
        }

        .mb0 {
            margin-bottom: 0;
        }

        .preheader {
            color: transparent;
            display: none;
            height: 0;
            max-height: 0;
            max-width: 0;
            opacity: 0;
            overflow: hidden;
            mso-hide: all;
            visibility: hidden;
            width: 0;
        }

        .powered-by a {
            text-decoration: none;
        }

        hr {
            border: 0;
            border-bottom: 1px solid #f6f6f6;
            margin: 20px 0;
        }

        /* -------------------------------------
          RESPONSIVE AND MOBILE FRIENDLY STYLES
      ------------------------------------- */
        @media only screen and (max-width: 620px) {
            table.body h1 {
                font-size: 28px !important;
                margin-bottom: 10px !important;
            }

            table.body p,
            table.body ul,
            table.body ol,
            table.body td,
            table.body span,
            table.body a {
                font-size: 16px !important;
            }

            table.body .wrapper,
            table.body .article {
                padding: 10px !important;
            }

            table.body .content {
                padding: 0 !important;
            }

            table.body .container {
                padding: 0 !important;
                width: 100% !important;
            }

            table.body .main {
                border-left-width: 0 !important;
                border-radius: 0 !important;
                border-right-width: 0 !important;
            }

            table.body .btn table {
                width: 100% !important;
            }

            table.body .btn a {
                width: 100% !important;
            }

            table.body .img-responsive {
                height: auto !important;
                max-width: 100% !important;
                width: auto !important;
            }
        }

        /* -------------------------------------
          PRESERVE THESE STYLES IN THE HEAD
      ------------------------------------- */
        @media all {
            .ExternalClass {
                width: 100%;
            }

            .ExternalClass,
            .ExternalClass p,
            .ExternalClass span,
            .ExternalClass font,
            .ExternalClass td,
            .ExternalClass div {
                line-height: 100%;
            }

            .apple-link a {
                color: inherit !important;
                font-family: inherit !important;
                font-size: inherit !important;
                font-weight: inherit !important;
                line-height: inherit !important;
                text-decoration: none !important;
            }

            #MessageViewBody a {
                color: inherit;
                text-decoration: none;
                font-size: inherit;
                font-family: inherit;
                font-weight: inherit;
                line-height: inherit;
            }

            .btn-primary table td:hover {
                background-color: #34495e !important;
            }

            .btn-primary a:hover {
                background-color: #34495e !important;
                border-color: #34495e !important;
            }
        }
    </style>
</head>

<body>
    <span class="preheader">Please Complete Performance Reviews</span>
    <table role="presentation" border="0" cellpadding="0" cellspacing="0" class="body">
        <tr>
            <td>&nbsp;</td>
            <td class="container">
                <div class="content">

                    <a href="https://fischerjordan.com" target="_blank"><img
                            src="https://fischerjordan.com/wp-content/uploads/2018/12/FJ-Logo-horizontal-white-1.png"
                            alt="Fischer Jordan"
                            style="width: 100%; max-width: 250px; height: auto; margin: auto; display: block; margin-bottom: 20px; margin-top: 20px;"
                            height="54" width="250"></a>

                    <!-- START CENTERED WHITE CONTAINER -->
                    <table role=" presentation" class="main">

                        <!-- START MAIN CONTENT AREA -->
                        <tr>
                            <td class="wrapper">
                                <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td>
                                            <!-- gold bold title text -->
                                            <h1
                                                style="color: #C3962C; font-weight: bold; font-size: xx-large; margin: 0; text-align: center; margin-bottom: 5px;">
                                                """+self.Title+"""</h1>
                                            """+self.message+"""
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- END MAIN CONTENT AREA -->
                    </table>
                    <!-- END CENTERED WHITE CONTAINER -->

                    <!-- START FOOTER -->
                    <div class="footer">
                        <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                            <!-- row of two link icons in the center of the page -->
                            <tr>

                                <td style="text-align: center; padding-left: 10px; padding-right: 10px;">
                                    <a href="https://www.linkedin.com/company/fischerjordan" target="_blank"><img
                                            src="https://drive.google.com/uc?export=view&id=14V0Lg0d9O5ymr4PeEPBGs4GMqglbUwhm"
                                            alt="linkedin" style="max-width: 30px; margin-right: 3px; margin-left: 3px;"
                                            height="30" width="30" /></a>
                                    <a href="https://www.instagram.com/fischerjordan_ny/?hl=en" target="_blank"><img
                                            src="https://drive.google.com/uc?export=view&id=1h3WsIz_Q7SW_rBcsG4OZWd8UqUHTYvdQ"
                                            alt="instagram" style="max-width: 30px; margin-right: 3px; margin-left: 3px;"
                                            height="30" width="30" /></a>
                                    <a href="https://twitter.com/fischerjordanny" target="_blank"><img
                                            src="https://drive.google.com/uc?export=view&id=1-xcmwNyrOUDxao_MWlx3WVHbwTiioy2U"
                                            alt="twitter" style="max-width: 30px; margin-right: 3px; margin-left: 3px;"
                                            height="30" width="30" /></a>
                                </td>


                            </tr>

                            <tr>
                                <td class="content-block">
                                    <span class="apple-link" style="color: #C3962C;">
                                        ® FischerJordan, LLC | 125 Maiden Lane, Suite 312, New
                                        York, NY 10038</span>
                                </td>
                            </tr>
                        </table>
                    </div>
                    <!-- END FOOTER -->

                </div>
            </td>
            <td>&nbsp;</td>
        </tr>
    </table>
</body>

</html>
        """
