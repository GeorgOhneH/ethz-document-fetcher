from moodle.parser import parse_main_page


async def producer(session, queue, id):
    async with session.get(f"https://moodle-app2.let.ethz.ch/course/view.php?id={id}") as response:
        text = await response.read()
    return await parse_main_page(session, queue, text)
