using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System.Threading;
using System.Threading.Tasks;

public class Stack : MonoBehaviour
{
    [Header("Stack values")]
    public int id;
    public Vector2Int pos;
    public int nItems = 0;
    public List<Object> items;
    public int maxItems = 5; // Set this to your desired maximum stack size

    [Header("Engine values")]
    public Enviroment parentEnv;
    
    private float verticalItemOffset = 0.2f; // Adjust this value as needed
    private float itemScale = 0.8f; // Adjust this value as needed

    private SemaphoreSlim dropLock = new SemaphoreSlim(1, 1);

    private void Awake()
    {
        transform.localScale = new Vector3(Enviroment.tileSize - 0.5f, Enviroment.tileSize / 2, Enviroment.tileSize - 0.5f);
    }

    public async Task<bool> TryAddItemAsync(Object item)
    {
        await dropLock.WaitAsync();
        try
        {
            if (nItems >= maxItems)
            {
                return false;
            }

            nItems++;
            items.Add(item);
            
            // Scale down and position the item
            item.transform.localScale *= itemScale;
            item.transform.position = transform.position + Vector3.up * (nItems * verticalItemOffset);
            
            // Disable item's collider
            Collider itemCollider = item.GetComponent<Collider>();
            if (itemCollider != null)
            {
                itemCollider.enabled = false;
            }

            // Change layer if stack is full
            if (nItems == maxItems)
            {
                gameObject.layer = LayerMask.NameToLayer("Obstacles");
            }

            return true;
        }
        finally
        {
            dropLock.Release();
        }
    }
}