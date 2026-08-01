from app.dice.utils.extract import _collect_easy_apply_job_ids_from_html


def test_collect_easy_apply_job_ids_from_html_detects_current_dice_apply_urls():
    html = """
    <script>
    self.__next_f.push([1,"58:[\\"$\\",\\"$L62\\",null,{\\"href\\":\\"/job-applications/665008cb-cf61-447b-b019-3afd03141986/wizard\\",\\"buttonText\\":\\"Easy Apply\\"}]"]);
    self.__next_f.push([1,"62:[\\"$\\",\\"$L62\\",null,{\\"href\\":\\"/job-applications/88c8819a-6156-4636-bcee-7a87029080cd/start-apply\\",\\"buttonText\\":\\"Easy Apply\\"}]"]);
    </script>
    """

    assert _collect_easy_apply_job_ids_from_html(html) == {
        "665008cb-cf61-447b-b019-3afd03141986",
        "88c8819a-6156-4636-bcee-7a87029080cd",
    }


def test_collect_easy_apply_job_ids_from_html_ignores_non_apply_links():
    html = """
    <script>
    self.__next_f.push([1,"44:[\\"$\\",\\"$L56\\",null,{\\"href\\":\\"/job-detail/665008cb-cf61-447b-b019-3afd03141986\\",\\"buttonText\\":\\"Apply\\"}]"]);
    </script>
    """

    assert _collect_easy_apply_job_ids_from_html(html) == set()
