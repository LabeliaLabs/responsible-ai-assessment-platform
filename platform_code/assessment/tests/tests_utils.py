from django.test import TestCase
from assessment.utils import markdownify_italic, markdownify_bold


class TestMarkdownify(TestCase):
    def setUp(self):
        self.text1 = "Bonjour *madame*"
        self.text2 = "Bonjour **madame**"
        self.text3 = "I **gonna** take _a break_"
        self.text4 = "This sentence is pointless :("
        self.text5 = "Thi*s definit**ly a ran'(dom _ sen***tence"
        self.text6 = "There **are** __bold__ *text* **EVERYWHERE** !!"

    def testBold(self):
        self.assertEqual(self.text1, markdownify_bold(self.text1))
        self.assertEqual(
            "Bonjour <strong>madame</strong>", markdownify_bold(self.text2)
        )
        self.assertEqual(
            "I <strong>gonna</strong> take _a break_", markdownify_bold(self.text3)
        )
        self.assertEqual(self.text4, markdownify_bold(self.text4))
        self.assertEqual(self.text5, markdownify_bold(self.text5))
        self.assertEqual(
            "There <strong>are</strong> <strong>bold</strong> *text* <strong>EVERYWHERE</strong> !!",
            markdownify_bold(self.text6),
        )

    def testItalic(self):
        self.assertEqual("Bonjour <i>madame</i>", markdownify_italic(self.text1))
        self.assertEqual(self.text2, markdownify_italic(self.text2))
        self.assertEqual(
            "I **gonna** take <i>a break</i>", markdownify_italic(self.text3)
        )
        self.assertEqual(self.text4, markdownify_italic(self.text4))
        self.assertEqual(self.text5, markdownify_italic(self.text5))

    def testCombined(self):
        self.assertEqual(
            "Bonjour <i>madame</i>", markdownify_italic(markdownify_bold(self.text1))
        )
        self.assertEqual(
            "Bonjour <strong>madame</strong>",
            markdownify_italic(markdownify_bold(self.text2)),
        )
        self.assertEqual(
            "I <strong>gonna</strong> take <i>a break</i>",
            markdownify_italic(markdownify_bold(self.text3)),
        )
        self.assertEqual(self.text4, markdownify_italic(markdownify_bold(self.text4)))
        self.assertEqual(self.text5, markdownify_italic(markdownify_bold(self.text5)))
        self.assertEqual(
            "There <strong>are</strong> <strong>bold</strong> <i>text</i> <strong>EVERYWHERE</strong> !!",
            markdownify_italic(markdownify_bold(self.text6)),
        )
