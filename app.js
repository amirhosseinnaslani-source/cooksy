const $ = id => document.getElementById(id);
const fmt = n => Number(n).toLocaleString('fa-IR');
const storageKey = 'cooksy-cart-v1';
let recipes = [];
let cart = {};
let audience = 'home';
let filter = 'همه';
let toastTimer;

try { const saved = JSON.parse(localStorage.getItem(storageKey) || '{}'); if (saved && typeof saved === 'object' && !Array.isArray(saved)) cart = saved; } catch {}
function safeText(s) { return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function save() { localStorage.setItem(storageKey, JSON.stringify(cart)); updateCart(); }
function notice(s) { const el=$('toast'); el.textContent=s; el.classList.add('show'); clearTimeout(toastTimer); toastTimer=setTimeout(()=>el.classList.remove('show'),3000); }
function changeAudience(kind) {
  audience=kind;
  document.querySelectorAll('.audience').forEach(el=>{let on=el.dataset.kind===kind;el.classList.toggle('active',on);el.setAttribute('aria-pressed',String(on));});
  $('audienceHint').textContent=kind==='home'?'🥣 مواد اولیه برای دورهمی و خانواده، دقیقا به اندازه نیازت':'🏢 سفارش گروهی مواد اولیه برای آشپزخانه شرکت و سازمان';
  $('customerType').value=kind;
  $('businessFields').hidden=kind!=='business';
}
function card(r) {
 const ingredients=r.ingredients.slice(0,3).map(i=>safeText(i.name)).join('، ');
 return `<article class="recipe-card"><div class="recipe-visual"><span aria-hidden="true">${r.emoji}</span><span class="recipe-category">${safeText(r.category)}</span></div><div class="recipe-info"><h3>${safeText(r.name)}</h3><p>${safeText(r.subtitle)}</p><div class="meta">⏱️ حدود ${fmt(r.minutes)} دقیقه زمان پخت</div><div class="ingredient-summary">داخل بسته: ${ingredients} و ...<br><span>مقدار مواد بر اساس تعداد نفرات محاسبه می شود.</span></div><div class="recipe-bottom"><div class="price">${fmt(r.unit_price)} <small>تومان / نفر (نمونه)</small></div><button class="add-button" data-add="${r.id}" type="button">+ افزودن به سبد</button></div></div></article>`;
}
function renderRecipes() {
 const items=recipes.filter(r=>filter==='همه'||r.category===filter);
 $('recipeGrid').innerHTML=items.map(card).join('') || '<p>غذایی پیدا نشد.</p>';
}
function updateCart() {
 const entries=Object.entries(cart).filter(([id,n])=>recipes.some(r=>r.id===id)&&Number.isInteger(n)&&n>0);
 const count=entries.reduce((s,[,n])=>s+n,0);
 $('cartCount').textContent=fmt(count);
 $('checkoutButton').disabled=!count;
 const total=entries.reduce((s,[id,n])=>s+recipes.find(r=>r.id===id).unit_price*n,0);
 $('cartTotal').textContent=fmt(total)+' تومان';
 $('cartContents').innerHTML=entries.length?entries.map(([id,n])=>{const r=recipes.find(r=>r.id===id);return `<div class="cart-item"><div class="cart-emoji">${r.emoji}</div><div class="cart-details"><strong>${safeText(r.name)}</strong><small>مواد لازم برای ${fmt(n)} نفر · ${fmt(n*r.unit_price)} تومان</small><div class="cart-controls"><div class="quantity"><button data-minus="${id}" aria-label="کم کردن تعداد" type="button">−</button><span>${fmt(n)} نفر</span><button data-plus="${id}" aria-label="افزودن تعداد" type="button">+</button></div><button class="remove" data-remove="${id}" type="button">حذف</button></div></div></div>`}).join(''):'<div class="empty-cart">🛒<strong>سبدت هنوز خالیه!</strong><p>از بین غذاها، خوشمزه ترین رو انتخاب کن.</p></div>';
}
function openCart(){ $('overlay').hidden=false; $('cartDrawer').classList.add('open'); $('cartDrawer').setAttribute('aria-hidden','false'); $('cartButton').setAttribute('aria-expanded','true'); $('closeCart').focus(); }
function closeAll(){ $('overlay').hidden=true; $('cartDrawer').classList.remove('open'); $('cartDrawer').setAttribute('aria-hidden','true'); $('cartButton').setAttribute('aria-expanded','false'); $('checkoutModal').hidden=true; }
document.querySelectorAll('.audience').forEach(btn=>btn.addEventListener('click',()=>changeAudience(btn.dataset.kind)));
document.querySelectorAll('.filter').forEach(btn=>btn.addEventListener('click',()=>{filter=btn.dataset.filter;document.querySelectorAll('.filter').forEach(x=>x.classList.toggle('active',x===btn));renderRecipes();}));
$('recipeGrid').addEventListener('click',e=>{let id=e.target.closest('[data-add]')?.dataset.add;if(!id)return;cart[id]=Math.min(100,(cart[id]||0)+1);save();notice('مواد '+recipes.find(r=>r.id===id).name+' به سبد اضافه شد 💚');});
$('cartContents').addEventListener('click',e=>{const btn=e.target.closest('button');if(!btn)return;let id=btn.dataset.plus||btn.dataset.minus||btn.dataset.remove;if(!id)return;if(btn.dataset.plus)cart[id]=Math.min(100,(cart[id]||0)+1);else if(btn.dataset.minus)cart[id]=Math.max(0,(cart[id]||0)-1);else delete cart[id];if(cart[id]===0)delete cart[id];save();});
$('cartButton').addEventListener('click',openCart);
$('closeCart').addEventListener('click',closeAll);
$('closeCheckout').addEventListener('click',closeAll);
$('overlay').addEventListener('click',closeAll);
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeAll();});
$('checkoutButton').addEventListener('click',()=>{if(!Object.keys(cart).length)return;$('cartDrawer').classList.remove('open');$('cartDrawer').setAttribute('aria-hidden','true');$('checkoutModal').hidden=false;$('formMessage').textContent='';$('customerType').value=audience;$('businessFields').hidden=audience!=='business';$('checkoutForm').querySelector('input[name="customer_name"]').focus();});
$('customerType').addEventListener('change',e=>{audience=e.target.value;$('businessFields').hidden=audience!=='business';});
$('checkoutForm').addEventListener('submit',async e=>{
 e.preventDefault();
 const form=e.currentTarget;
 const data=Object.fromEntries(new FormData(form).entries());
 if(data.customer_type==='business'&&(!data.company_name?.trim()||!data.contact_name?.trim())){$('formMessage').textContent='نام شرکت و رابط را وارد کنید.';return;}
 data.items=Object.entries(cart).filter(([,n])=>Number.isInteger(n)&&n>0).map(([id,servings])=>({id,servings}));
 if(!data.items.length)return;
 const button=$('submitOrder');button.disabled=true;button.textContent='در حال ثبت...';$('formMessage').textContent='';
 try{
  const response=await fetch('/api/orders',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  const result=await response.json();
  if(!response.ok)throw new Error(result.error||'ثبت سفارش انجام نشد.');
  $('formMessage').classList.add('success');$('formMessage').textContent='✅ درخواست شماره '+fmt(result.order_id)+' ثبت شد! برای تایید قیمت و تحویل با شما تماس می گیریم.';
  cart={};save();form.reset();$('checkoutForm').querySelectorAll('input,textarea,select').forEach(x=>x.disabled=true);button.textContent='درخواست ثبت شد';
 }catch(error){$('formMessage').classList.remove('success');$('formMessage').textContent=error.message;button.disabled=false;button.textContent='ثبت درخواست سفارش ←';}
});
fetch('/api/recipes').then(r=>{if(!r.ok)throw Error();return r.json()}).then(data=>{recipes=data.recipes;renderRecipes();updateCart()}).catch(()=>{$('recipeGrid').innerHTML='<p>فعلا دریافت منو ممکن نیست. لطفا صفحه را دوباره باز کنید.</p>';});
changeAudience('home');
