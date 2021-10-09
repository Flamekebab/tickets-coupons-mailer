This is a collection of things I wrote for Vowley Races in 2020. It's not actually the complete collection as there's also a coupon creator for the Wingbeat website. I'd include it but it's written in PHP and I'd rather not have multiple languages in the same repo, at least for now!

#### Broad strokes explanation of what's in here, mainly for my future self:
The Vowley website had a WordPress-based registration form. People would fill it out to express an interest, I think? If they were planning to compete they'd get sent a coupon for money off a Roprey model from Wingbeat.

The coupon creation wasn't fully automated - instead they'd be created in batches. That's what the PHP script would do - take their data, filter out the relevant entries and then talk to the WooCommerce API to generate coupons. These would then be emailed out.

Closer to the event I then put together something that would email out tickets to everyone attending (whether their tickets were paid, complimentary, or provided through another company's hospitality buy). The emails were sent as both plain text and HTML, talking to the company mail server to send them.

That wasn't the only use for the ticket/pre-reg information though - the data was also used for planning by some of the Vowley staff. Initially I was downloading CSV files from the website and running them through the form-data-processor.py script. Then I had words with the API and had it download the data for me. Then I decided to get ambitious and provide a means for the Vowley staff to grab their own data by means of a Windows program with a GUI. That's form-data-processor-gui.py (and why there's a thing in there that would email me if it failed).