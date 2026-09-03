/* Restaure les deux affiches effacees le 3 septembre 2026.
 *
 * A COLLER dans la console du navigateur, sur la page /admin, EN ETANT
 * CONNECTE : l appel emprunte la session du navigateur, il n y a donc aucun
 * mot de passe a saisir ni a confier.
 *
 * Les deux entrees sont recopiees a l identique — meme identifiant, meme
 * texte, meme affiche, meme date de fin. Leurs images n ont jamais quitte le
 * magasin : seules leurs fiches avaient disparu.
 *
 * Chrome : F12, onglet Console, coller, Entree.
 */
(async () => {
  const AFFICHES = [
    {
      id: '30abbcae-3344-43a2-a7a4-e052e68914f8',
      titre: 'Saint-Sylvestre',
      accent: '', categorie: '', badge: '',
      texte: "Dîner de fin d'année au bord de la lagune, puis la nuit au "
           + 'night-club. Les chambres partent tôt sur cette date.',
      cta: 'Réserver maintenant',
      href: 'reserver.html',
      fond: 'https://qjatdj8uw2dzupim.public.blob.vercel-storage.com/evannath/'
          + 'affiches/1788346434609-2b963550-2YzznJfYJxGZ8Dd1GP11uTboWAIg1q.jpeg',
      format: 'affiche',
      quand: 'Du 31 décembre au 01 janvier 2027',
      fin: '2027-01-02',
      publie: true,
      infos: [],
    },
    {
      id: 'a588efc1-ba81-432c-9af3-8939259c3275',
      titre: 'Offre Exclusive',
      accent: '', categorie: '', badge: '',
      texte: 'Plaisir garanti ! 😍 Offrez-vous un séjour de rêve à '
           + "l'Evannath Hôtel avec 15% de remise sur toutes nos chambres "
           + 'jusqu’au 7 juin. 🛏️✨ Confort et évasion assurés. '
           + 'Profitez-en vite !',
      cta: 'Réserver maintenant',
      href: 'reserver.html',
      fond: 'https://qjatdj8uw2dzupim.public.blob.vercel-storage.com/evannath/'
          + 'affiches/1788350142765-4d5d6712-Uwrkr5NEqPzI3OOtZsGlzf2cZXXAAS.jpeg',
      format: 'affiche',
      quand: 'Du 1er au 17 Juin',
      fin: '2027-06-18',
      publie: true,
      infos: [],
    },
  ];

  /* On verifie AVANT d ecrire : si la lecture est en defaut, une ecriture
     effacerait ce qui reste. C est precisement ce qui a cause la perte. */
  const etat = await (await fetch('/api/admin?a=etat')).json();
  if (!etat.ok) {
    console.error('Connectez-vous d abord sur /admin, puis recollez ceci.');
    return;
  }
  if (etat.panne) {
    console.error('Le stockage ne repond pas :', etat.panne,
      '\nN ecrivez rien. Rechargez dans une minute et reessayez.');
    return;
  }
  console.log('Stockage :', etat.stockage, '| version', etat.version,
    '| evenements avant :', etat.evenements);

  for (const entree of AFFICHES) {
    const r = await fetch('/api/admin?a=enregistrer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'evenement', entree }),
    });
    const j = await r.json().catch(() => ({}));
    console.log(r.ok ? 'restauree :' : 'ECHEC :', entree.titre,
      r.ok ? '' : (j.message || r.status));
    if (!r.ok) return;
  }

  const apres = await (await fetch('/api/admin?a=public&x=' + Date.now())).json();
  console.log('Evenements en ligne :', (apres.evenements || []).length);
  console.log('Rechargez la page d administration.');
})();
